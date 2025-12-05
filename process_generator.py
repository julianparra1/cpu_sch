"""
process_generator.py - Cliente CLI para Generacion de Procesos

Herramienta de linea de comandos que permite:
1. Conectar al servidor de scheduling
2. Agregar procesos de forma interactiva
3. Controlar la simulacion remotamente
4. Demostrar comunicacion IPC desde multiples clientes

Este cliente es complementario al cliente grafico (client.py).
Ambos pueden conectarse simultaneamente al servidor, demostrando
la capacidad multicliente del sistema.

Comandos disponibles:
  add <nombre> <burst> [arrival] [priority] - Agregar proceso
  random / r                                - Proceso aleatorio
  batch <n>                                 - Agregar n procesos
  algo <FCFS|SJF|PRIORITY|RR>               - Cambiar algoritmo
  quantum <valor>                           - Establecer quantum
  start                                     - Iniciar simulacion
  pause                                     - Pausar/Reanudar
  reset                                     - Reiniciar simulacion
  quit / q                                  - Salir

Autor: Julian Parra
Proyecto: Simulador de Scheduling de CPU
Materia: Sistemas Operativos - UABC 2025
"""

import socket
import time
import random
import sys
from typing import Optional

from config import SERVER_HOST, SERVER_PORT, BUFFER_SIZE
from protocol import Protocol, MessageBuffer


class ProcessGenerator:
    """
    Cliente CLI para generacion y control de procesos.
    
    Permite interactuar con el servidor de scheduling desde
    la terminal, enviando comandos para:
    - Crear procesos individuales o en lote
    - Cambiar algoritmo de scheduling
    - Controlar ejecucion de la simulacion
    
    Util para:
    - Testing y depuracion
    - Demostracion de arquitectura multicliente
    - Scripting de escenarios de prueba
    """
    
    def __init__(self, host: str = SERVER_HOST, port: int = SERVER_PORT):
        """
        Inicializa el generador.
        
        Args:
            host: IP del servidor
            port: Puerto del servidor
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        
        # Nombres de servicios comunes para procesos aleatorios
        self._process_names = [
            "Apache", "Nginx", "MySQL", "PostgreSQL", "MongoDB",
            "Redis", "Elasticsearch", "Kafka", "RabbitMQ", "Jenkins",
            "Docker", "Kubernetes", "Terraform", "Ansible", "Prometheus"
        ]
        self._idx = 0
    
    def connect(self) -> bool:
        """
        Establece conexion con el servidor.
        
        Returns:
            True si la conexion fue exitosa
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"[+] Conectado al servidor {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[!] Error: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del servidor."""
        if self.socket and self.connected:
            try:
                self.socket.send(Protocol.disconnect().to_bytes())
                self.socket.close()
            except:
                pass
            self.connected = False
    
    def add_process(self, name: str, burst: int, arrival: int = 0, priority: int = 5):
        """
        Agrega un proceso al servidor.
        
        Args:
            name:     Nombre del proceso
            burst:    Tiempo de CPU requerido
            arrival:  Tiempo de llegada (default: 0)
            priority: Prioridad 1-10 (default: 5)
        """
        if not self.connected:
            return
        
        msg = Protocol.add_process(name, burst, arrival, priority)
        self.socket.send(msg.to_bytes())
        print(f"[>] Proceso enviado: {name} (burst={burst}, arrival={arrival}, priority={priority})")
    
    def add_random_process(self):
        """Agrega un proceso con valores aleatorios."""
        name = self._process_names[self._idx % len(self._process_names)]
        self._idx += 1
        burst = random.randint(2, 15)
        priority = random.randint(1, 10)
        
        self.add_process(name, burst, 0, priority)
    
    def run_interactive(self):
        """
        Inicia el modo interactivo.
        
        Lee comandos de stdin y los procesa hasta que el
        usuario escribe 'quit' o presiona Ctrl+C.
        """
        if not self.connect():
            return
        
        self._print_help_banner()
        
        try:
            while self.connected:
                try:
                    cmd = input("\n> ").strip().lower().split()
                    if not cmd:
                        continue
                    
                    self._process_command(cmd)
                    
                except ValueError as e:
                    print(f"[!] Error en el valor: {e}")
                except socket.error as e:
                    print(f"[!] Error de conexion: {e}")
                    self.connected = False
                    
        except KeyboardInterrupt:
            print("\n[*] Interrupcion")
        except EOFError:
            print("\n[*] Fin de entrada")
        finally:
            self.disconnect()
            print("[*] Generador cerrado")
    
    def _process_command(self, cmd: list):
        """
        Procesa un comando del usuario.
        
        Args:
            cmd: Lista de tokens del comando
        """
        action = cmd[0]
        
        # Comandos de salida
        if action in ('quit', 'exit', 'q'):
            self.connected = False
            return
        
        # Agregar proceso manual
        if action == 'add' and len(cmd) >= 3:
            name = cmd[1]
            burst = int(cmd[2])
            arrival = int(cmd[3]) if len(cmd) > 3 else 0
            priority = int(cmd[4]) if len(cmd) > 4 else 5
            self.add_process(name, burst, arrival, priority)
        
        # Proceso aleatorio
        elif action in ('random', 'r'):
            self.add_random_process()
        
        # Lote de procesos
        elif action == 'batch' and len(cmd) >= 2:
            count = int(cmd[1])
            print(f"[*] Agregando {count} procesos...")
            for i in range(count):
                self.add_random_process()
                time.sleep(0.1)
            print(f"[OK] {count} procesos agregados")
        
        # Cambiar algoritmo
        elif action == 'algo' and len(cmd) >= 2:
            algo = cmd[1].upper()
            msg = Protocol.set_algorithm(algo)
            self.socket.send(msg.to_bytes())
            print(f"[>] Algoritmo cambiado a: {algo}")
        
        # Establecer quantum
        elif action == 'quantum' and len(cmd) >= 2:
            q = int(cmd[1])
            msg = Protocol.set_quantum(q)
            self.socket.send(msg.to_bytes())
            print(f"[>] Quantum establecido: {q}")
        
        # Control de simulacion
        elif action == 'start':
            msg = Protocol.start_simulation()
            self.socket.send(msg.to_bytes())
            print("[>] Simulacion iniciada")
        
        elif action == 'pause':
            msg = Protocol.pause_simulation()
            self.socket.send(msg.to_bytes())
            print("[>] Pausar/Reanudar enviado")
        
        elif action == 'reset':
            msg = Protocol.reset_simulation()
            self.socket.send(msg.to_bytes())
            print("[>] Simulacion reiniciada")
        
        elif action == 'help':
            self._print_help()
        
        else:
            print("[?] Comando no reconocido. Escribe 'help' para ver comandos.")
    
    def _print_help_banner(self):
        """Imprime el banner inicial con comandos disponibles."""
        print("""
========================================================
     GENERADOR DE PROCESOS REMOTO
========================================================
  Comandos:
    add <nombre> <burst> [arrival] [priority]
    random                    - Agregar proceso aleatorio
    batch <cantidad>          - Agregar varios aleatorios
    algo <FCFS|SJF|PRIORITY|RR> - Cambiar algoritmo
    quantum <valor>           - Establecer quantum
    start                     - Iniciar simulacion
    pause                     - Pausar/Reanudar
    reset                     - Reiniciar simulacion
    quit                      - Salir
========================================================
        """)
    
    def _print_help(self):
        """Imprime ayuda detallada de comandos."""
        print("""
Comandos disponibles:
  add <nombre> <burst> [arrival] [priority] - Agregar proceso
  random (r)                                - Proceso aleatorio
  batch <n>                                 - Agregar n procesos
  algo <FCFS|SJF|PRIORITY|RR>               - Cambiar algoritmo
  quantum <valor>                           - Establecer quantum
  start                                     - Iniciar
  pause                                     - Pausar/Reanudar
  reset                                     - Reiniciar
  quit (q)                                  - Salir
        """)


def main():
    """Punto de entrada del generador de procesos."""
    generator = ProcessGenerator()
    generator.run_interactive()


if __name__ == "__main__":
    main()
