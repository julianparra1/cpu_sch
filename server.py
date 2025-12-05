"""
server.py - Servidor TCP del Simulador de Scheduling

Componente principal del backend que:
1. Escucha conexiones TCP en localhost:5555
2. Maneja multiples clientes con threading
3. Ejecuta el loop de simulacion
4. Broadcast del estado a todos los clientes conectados

Arquitectura:
- Thread principal: acepta conexiones entrantes
- Thread por cliente: recibe y procesa mensajes
- Thread de simulacion: ejecuta ticks periodicos

Protocolo:
- Mensajes JSON delimitados por newline
- Cliente envia comandos (ADD, START, PAUSE, ALGO, etc.)
- Servidor responde con STATE_UPDATE

Autor: Julian Parra
Proyecto: Simulador de Scheduling de CPU
Materia: Sistemas Operativos - UABC 2025
"""

import socket
import threading
import json
import time
import signal
import sys
from typing import Dict, Optional

from config import SERVER_HOST, SERVER_PORT, MAX_CLIENTS, BUFFER_SIZE, MSG_TYPES
from protocol import Message, Protocol, MessageBuffer
from scheduling_algorithms import SchedulerManager
from process import Process


class SchedulingServer:
    """
    Servidor TCP multicliente para el simulador de scheduling.
    
    Responsabilidades:
    - Gestionar conexiones TCP de clientes
    - Procesar comandos de control (ADD, START, PAUSE, RESET, ALGO)
    - Ejecutar la logica de scheduling via SchedulerManager
    - Sincronizar estado entre todos los clientes conectados
    
    Threading model:
    - Main thread:       Acepta conexiones (blocking con timeout)
    - Client threads:    Un thread por cliente para recv()
    - Simulation thread: Ejecuta ticks cada 500ms
    
    Sincronizacion:
    - self.lock protege acceso a clients dict y scheduler
    - _shutdown_event coordina shutdown limpio de todos los threads
    """
    
    def __init__(self, host: str = SERVER_HOST, port: int = SERVER_PORT):
        """
        Inicializa el servidor.
        
        Args:
            host: IP a bindear (default: localhost)
            port: Puerto TCP (default: 5555)
        """
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        
        # Diccionario de clientes: client_id -> socket
        self.clients: Dict[str, socket.socket] = {}
        self.client_buffers: Dict[str, MessageBuffer] = {}
        
        # Motor de scheduling
        self.scheduler = SchedulerManager()
        
        # Control de estado
        self.running = False
        self.lock = threading.Lock()
        self._next_pid = 1
        self._sim_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
    def start(self):
        """
        Inicia el servidor y comienza a aceptar conexiones.
        
        Proceso:
        1. Crear socket TCP y bindear al puerto
        2. Iniciar thread de simulacion
        3. Loop infinito aceptando conexiones
        4. Por cada conexion, spawn thread de manejo
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Timeout permite verificar shutdown periodicamente
        self.server_socket.settimeout(1.0)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(MAX_CLIENTS)
            self.running = True
            
            print(f"""
========================================================
     SERVIDOR DE SCHEDULING INICIADO
========================================================
  Host: {self.host}    Puerto: {self.port}
  Esperando conexiones...
  
  Presiona Ctrl+C para detener el servidor
========================================================
            """)
            
            # Thread de simulacion ejecuta ticks periodicos
            self._sim_thread = threading.Thread(
                target=self._simulation_loop, 
                daemon=True,
                name="SimulationThread"
            )
            self._sim_thread.start()
            
            # Loop principal: aceptar conexiones
            while self.running and not self._shutdown_event.is_set():
                try:
                    client_socket, address = self.server_socket.accept()
                    client_id = f"{address[0]}:{address[1]}"
                    
                    with self.lock:
                        self.clients[client_id] = client_socket
                        self.client_buffers[client_id] = MessageBuffer()
                    
                    print(f"[+] Cliente conectado: {client_id}")
                    
                    # Thread dedicado para este cliente
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_id, client_socket),
                        daemon=True,
                        name=f"Client-{client_id}"
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    # Timeout normal, verificar condiciones de shutdown
                    continue
                except socket.error as e:
                    if self.running and not self._shutdown_event.is_set():
                        print(f"[!] Error aceptando conexion: {e}")
                        
        except Exception as e:
            print(f"[!] Error iniciando servidor: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """
        Detiene el servidor de forma limpia.
        
        1. Senala shutdown a todos los threads
        2. Cierra sockets de clientes
        3. Cierra socket del servidor
        """
        if self._shutdown_event.is_set():
            return
        
        print("\n[*] Deteniendo servidor...")
        self._shutdown_event.set()
        self.running = False
        
        with self.lock:
            for client_id, client_socket in list(self.clients.items()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("[*] Servidor detenido")
    
    def _handle_client(self, client_id: str, client_socket: socket.socket):
        """
        Maneja la comunicacion con un cliente especifico.
        
        Este metodo corre en un thread dedicado por cliente.
        
        Loop:
        1. Recibir datos del socket
        2. Parsear mensajes con MessageBuffer
        3. Procesar cada mensaje
        4. Terminar si desconexion o error
        
        Args:
            client_id:     Identificador del cliente (ip:port)
            client_socket: Socket TCP del cliente
        """
        buffer = self.client_buffers[client_id]
        
        # Enviar estado inicial al conectarse
        self._send_to_client(client_id, Protocol.state_update(self.scheduler.get_state()))
        
        try:
            while self.running:
                try:
                    data = client_socket.recv(BUFFER_SIZE)
                    if not data:
                        # Conexion cerrada por el cliente
                        break
                    
                    # Parsear mensajes del stream TCP
                    messages = buffer.add_data(data)
                    should_continue = True
                    
                    for msg in messages:
                        result = self._process_message(client_id, msg)
                        if result is False:
                            # Cliente solicito desconexion (BYE)
                            should_continue = False
                            break
                    
                    if not should_continue:
                        break
                        
                except socket.error:
                    break
                    
        except Exception as e:
            print(f"[!] Error con cliente {client_id}: {e}")
        finally:
            self._disconnect_client(client_id)
    
    def _process_message(self, client_id: str, msg: Message):
        """
        Procesa un mensaje recibido de un cliente.
        
        Tipos de mensaje soportados:
        - ADD_PROCESS:    Crea un nuevo proceso
        - REMOVE_PROCESS: Elimina proceso por PID
        - START_SIM:      Inicia la simulacion
        - PAUSE_SIM:      Pausa/reanuda
        - RESET_SIM:      Reinicia a tiempo 0
        - SET_ALGORITHM:  Cambia algoritmo de scheduling
        - SET_QUANTUM:    Configura quantum para Round Robin
        - GET_STATE:      Solicita estado actual
        - TICK:           Tick manual (debug)
        - DISCONNECT:     Cliente quiere desconectarse
        
        Returns:
            False si el cliente quiere desconectarse, True en otro caso
        """
        msg_type = msg.type
        data = msg.data
        
        print(f"[<] {client_id}: {msg_type}")
        
        with self.lock:
            if msg_type == MSG_TYPES['ADD_PROCESS']:
                process = Process(
                    pid=self._next_pid,
                    name=data.get('name', f'P{self._next_pid}'),
                    burst_time=data.get('burst_time', 5),
                    arrival_time=data.get('arrival_time', self.scheduler.current_time),
                    priority=data.get('priority', 5)
                )
                self.scheduler.add_process(process)
                self._next_pid += 1
                print(f"    [+] Proceso agregado: {process}")
                self._broadcast_state()
                
            elif msg_type == MSG_TYPES['REMOVE_PROCESS']:
                pid = data.get('pid')
                if self.scheduler.remove_process(pid):
                    print(f"    [-] Proceso {pid} removido")
                self._broadcast_state()
                
            elif msg_type == MSG_TYPES['START_SIM']:
                self.scheduler.start()
                print("    [>] Simulacion iniciada")
                self._broadcast_state()
                
            elif msg_type == MSG_TYPES['PAUSE_SIM']:
                if self.scheduler.is_paused:
                    self.scheduler.resume()
                    print("    [>] Simulacion reanudada")
                else:
                    self.scheduler.pause()
                    print("    [||] Simulacion pausada")
                self._broadcast_state()
                
            elif msg_type == MSG_TYPES['RESET_SIM']:
                self.scheduler.reset()
                self._next_pid = 1
                print("    [R] Simulacion reiniciada")
                self._broadcast_state()
                
            elif msg_type == MSG_TYPES['SET_ALGORITHM']:
                algo = data.get('algorithm', 'FCFS')
                if self.scheduler.set_algorithm(algo):
                    print(f"    [*] Algoritmo cambiado a: {algo}")
                self._broadcast_state()
                
            elif msg_type == MSG_TYPES['SET_QUANTUM']:
                quantum = data.get('quantum', 2)
                self.scheduler.set_quantum(quantum)
                print(f"    [*] Quantum establecido a: {quantum}")
                self._broadcast_state()
                
            elif msg_type == MSG_TYPES['GET_STATE']:
                self._send_to_client(client_id, Protocol.state_update(self.scheduler.get_state()))
                
            elif msg_type == MSG_TYPES['TICK']:
                self.scheduler.tick()
                self._broadcast_state()
                
            elif msg_type == MSG_TYPES['DISCONNECT']:
                # Retornar False indica al caller que debe terminar el loop
                # No llamar _disconnect_client aqui porque tenemos el lock
                return False
        
        return True
    
    def _simulation_loop(self):
        """
        Loop de simulacion que ejecuta ticks periodicos.
        
        Corre en thread separado. Cada 500ms:
        1. Verifica si la simulacion esta activa
        2. Ejecuta un tick del scheduler
        3. Broadcast del nuevo estado a clientes
        """
        tick_interval = 0.5
        
        while self.running:
            time.sleep(tick_interval)
            
            with self.lock:
                if self.scheduler.is_running and not self.scheduler.is_paused:
                    old_time = self.scheduler.current_time
                    self.scheduler.tick()
                    
                    if self.scheduler.current_time != old_time:
                        self._broadcast_state()
    
    def _send_to_client(self, client_id: str, msg: Message):
        """Envia un mensaje a un cliente especifico."""
        if client_id in self.clients:
            try:
                self.clients[client_id].send(msg.to_bytes())
            except socket.error:
                self._disconnect_client(client_id)
    
    def _broadcast_state(self):
        """
        Envia el estado actual a todos los clientes conectados.
        
        Esto sincroniza la vista de todos los clientes:
        - Tiempo actual
        - Lista de procesos
        - Proceso en ejecucion
        - Gantt chart
        - Estadisticas
        """
        state_msg = Protocol.state_update(self.scheduler.get_state())
        disconnected = []
        
        for client_id, client_socket in list(self.clients.items()):
            try:
                client_socket.send(state_msg.to_bytes())
            except socket.error:
                disconnected.append(client_id)
        
        for client_id in disconnected:
            self._disconnect_client(client_id)
    
    def _disconnect_client(self, client_id: str):
        """Desconecta un cliente y limpia sus recursos."""
        with self.lock:
            if client_id in self.clients:
                try:
                    self.clients[client_id].close()
                except:
                    pass
                del self.clients[client_id]
                if client_id in self.client_buffers:
                    del self.client_buffers[client_id]
                print(f"[-] Cliente desconectado: {client_id}")


def main():
    """Punto de entrada del servidor."""
    server = SchedulingServer()
    
    def signal_handler(sig, frame):
        """Maneja Ctrl+C para shutdown limpio."""
        server.stop()
        import os
        os._exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
