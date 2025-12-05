"""
client.py - Cliente Grafico del Simulador de Scheduling

Cliente PyGame que:
1. Se conecta al servidor via socket TCP
2. Envia comandos de control del usuario
3. Recibe actualizaciones de estado
4. Renderiza la interfaz grafica

Controles:
- [1-4]   Seleccionar algoritmo (FCFS, SJF, Priority, RR)
- [SPACE] Iniciar/Pausar simulacion
- [A]     Agregar proceso aleatorio
- [R]     Reiniciar simulacion
- [+/-]   Ajustar quantum (Round Robin)
- [Q/ESC] Salir

Arquitectura:
- Non-blocking socket para recibir sin bloquear el render loop
- Estado sincronizado desde el servidor via STATE_UPDATE
- Rendering delegado a la clase Renderer

Autor: Julian Parra
Proyecto: Simulador de Scheduling de CPU
Materia: Sistemas Operativos - UABC 2025
"""

import socket
import threading
import pygame
import random
import sys
import time
from typing import Optional, List

from config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE, MSG_TYPES, DEFAULT_QUANTUM
from protocol import Message, Protocol, MessageBuffer
from visualization import Renderer


class SchedulingClient:
    """
    Cliente grafico para el simulador de scheduling.
    
    Responsabilidades:
    - Conexion TCP al servidor
    - Captura de entrada del usuario (teclado)
    - Envio de comandos al servidor
    - Recepcion de estado actualizado
    - Delegacion de rendering a Renderer
    
    Modelo de ejecucion:
    - Single thread con socket non-blocking
    - Game loop: input -> network -> render
    """
    
    def __init__(self, host: str = SERVER_HOST, port: int = SERVER_PORT):
        """
        Inicializa el cliente.
        
        Args:
            host: IP del servidor
            port: Puerto del servidor
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False
        
        # Estado recibido del servidor
        self.state = {
            'current_time': 0,
            'algorithm': 'FCFS',
            'algorithm_desc': '',
            'is_running': False,
            'is_paused': False,
            'running_process': None,
            'processes': [],
            'gantt_chart': [],
            'statistics': {},
            'context_switches': 0
        }
        self.state_lock = threading.Lock()
        
        # Buffer para parsear mensajes del stream TCP
        self.buffer = MessageBuffer()
        
        # Componente de rendering
        self.renderer: Optional[Renderer] = None
        
        # Configuracion local del quantum
        self.quantum = DEFAULT_QUANTUM
        
        # Nombres realistas para procesos aleatorios
        self._process_names = [
            "Chrome", "Firefox", "Code", "Terminal", "Spotify", 
            "Discord", "Slack", "Zoom", "Python", "Node",
            "Docker", "Git", "Bash", "MySQL", "Redis",
            "Nginx", "Apache", "Java", "Rust", "Go"
        ]
        self._next_name_idx = 0
    
    def connect(self) -> bool:
        """
        Establece conexion TCP con el servidor.
        
        Returns:
            True si la conexion fue exitosa
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            
            # Non-blocking permite polling en el game loop
            self.socket.setblocking(False)
            self.connected = True
            print(f"[+] Conectado al servidor {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[!] Error conectando al servidor: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del servidor de forma limpia."""
        if self.socket and self.connected:
            try:
                # Notificar al servidor
                self.send_message(Protocol.disconnect())
                self.socket.close()
            except:
                pass
            self.connected = False
            print("[-] Desconectado del servidor")
    
    def send_message(self, msg: Message):
        """
        Envia un mensaje al servidor.
        
        Args:
            msg: Mensaje a enviar (se serializa a JSON)
        """
        if self.socket and self.connected:
            try:
                self.socket.send(msg.to_bytes())
            except socket.error as e:
                print(f"[!] Error enviando mensaje: {e}")
                self.connected = False
    
    def receive_messages(self) -> List[Message]:
        """
        Recibe mensajes pendientes del servidor (non-blocking).
        
        El socket esta en modo non-blocking, asi que retorna
        inmediatamente si no hay datos disponibles.
        
        Returns:
            Lista de mensajes recibidos (puede estar vacia)
        """
        messages = []
        if self.socket and self.connected:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if data:
                    messages = self.buffer.add_data(data)
                elif data == b'':
                    # Conexion cerrada por el servidor
                    self.connected = False
            except BlockingIOError:
                # No hay datos disponibles
                pass
            except socket.error:
                self.connected = False
        return messages
    
    def process_server_messages(self):
        """
        Procesa mensajes recibidos del servidor.
        
        El mensaje principal es STATE_UPDATE que contiene:
        - Tiempo actual
        - Algoritmo activo
        - Lista de procesos
        - Gantt chart
        - Estadisticas
        """
        messages = self.receive_messages()
        
        for msg in messages:
            if msg.type == MSG_TYPES['STATE_UPDATE']:
                with self.state_lock:
                    self.state = msg.data
            elif msg.type == MSG_TYPES['DISCONNECT']:
                self.connected = False
                print("[!] Servidor desconectado")
    
    def add_random_process(self):
        """
        Agrega un proceso con valores aleatorios.
        
        Genera:
        - Nombre: de lista de aplicaciones comunes
        - Burst time: 2-12 unidades
        - Arrival time: tiempo actual
        - Priority: 1-10
        """
        name = self._process_names[self._next_name_idx % len(self._process_names)]
        self._next_name_idx += 1
        
        burst = random.randint(2, 12)
        arrival = self.state.get('current_time', 0)
        priority = random.randint(1, 10)
        
        self.send_message(Protocol.add_process(name, burst, arrival, priority))
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """
        Procesa un evento de entrada del usuario.
        
        Mapeo de teclas:
        - 1-4:     Algoritmos (FCFS, SJF, Priority, RR)
        - SPACE:   Start/Pause
        - A:       Add process
        - R:       Reset
        - +/-:     Quantum adjustment
        - Q/ESC:   Quit
        
        Args:
            event: Evento de PyGame
            
        Returns:
            False si debe cerrar la aplicacion
        """
        if event.type == pygame.QUIT:
            return False
        
        if event.type == pygame.KEYDOWN:
            # Seleccion de algoritmo
            if event.key == pygame.K_1:
                self.send_message(Protocol.set_algorithm('FCFS'))
            elif event.key == pygame.K_2:
                self.send_message(Protocol.set_algorithm('SJF'))
            elif event.key == pygame.K_3:
                self.send_message(Protocol.set_algorithm('PRIORITY'))
            elif event.key == pygame.K_4:
                self.send_message(Protocol.set_algorithm('RR'))
                self.send_message(Protocol.set_quantum(self.quantum))
            
            # Control de simulacion
            elif event.key == pygame.K_SPACE:
                if not self.state.get('is_running'):
                    self.send_message(Protocol.start_simulation())
                else:
                    self.send_message(Protocol.pause_simulation())
            
            elif event.key == pygame.K_r:
                self.send_message(Protocol.reset_simulation())
            
            elif event.key == pygame.K_a:
                self.add_random_process()
            
            # Ajuste de quantum
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.quantum = min(10, self.quantum + 1)
                self.send_message(Protocol.set_quantum(self.quantum))
                if self.renderer:
                    self.renderer.quantum = self.quantum
            
            elif event.key == pygame.K_MINUS:
                self.quantum = max(1, self.quantum - 1)
                self.send_message(Protocol.set_quantum(self.quantum))
                if self.renderer:
                    self.renderer.quantum = self.quantum
            
            # Salir
            elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                return False
        
        return True
    
    def run(self):
        """
        Loop principal del cliente.
        
        1. Conectar al servidor
        2. Inicializar renderer PyGame
        3. Game loop:
           a. Recibir mensajes del servidor
           b. Procesar input del usuario
           c. Renderizar frame
        4. Cleanup al salir
        """
        if not self.connect():
            print("[!] No se pudo conectar al servidor. Asegurate de que esta corriendo.")
            print("    Ejecuta: python server.py")
            return
        
        self.renderer = Renderer()
        self.running = True
        
        print("""
========================================================
     CLIENTE DE SCHEDULING INICIADO
========================================================
  Controles:
    [1-4] Cambiar algoritmo
    [SPACE] Iniciar/Pausar
    [A] Agregar proceso aleatorio
    [R] Reiniciar simulacion
    [+/-] Ajustar quantum (Round Robin)
    [Q/ESC] Salir
========================================================
        """)
        
        try:
            while self.running and self.connected:
                # 1. Recibir actualizaciones del servidor
                self.process_server_messages()
                
                # 2. Procesar eventos de usuario
                for event in self.renderer.get_events():
                    if not self.handle_input(event):
                        self.running = False
                        break
                
                # 3. Renderizar frame actual
                with self.state_lock:
                    self.renderer.render(self.state)
                
        except KeyboardInterrupt:
            print("\n[*] Interrupcion recibida")
        finally:
            self.disconnect()
            if self.renderer:
                self.renderer.quit()
            print("[*] Cliente cerrado")


def main():
    """Punto de entrada del cliente."""
    client = SchedulingClient()
    client.run()


if __name__ == "__main__":
    main()
