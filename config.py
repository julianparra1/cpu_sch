"""
config.py - Configuracion central del Simulador de Scheduling

Este modulo contiene todas las constantes de configuracion utilizadas
por el servidor, cliente y algoritmos de scheduling. Centralizar la
configuracion facilita el ajuste de parametros sin modificar el codigo.

Autor: Julian Parra
Proyecto: Simulador de Scheduling de CPU
Materia: Sistemas Operativos - UABC 2025
"""

# ==============================================================================
# CONFIGURACION DE RED (IPC via Sockets TCP)
# ==============================================================================

SERVER_HOST = 'localhost'   # Direccion del servidor
SERVER_PORT = 5555          # Puerto TCP para conexiones
MAX_CLIENTS = 10            # Maximo de clientes simultaneos
BUFFER_SIZE = 4096          # Tamano del buffer de recepcion en bytes

# ==============================================================================
# CONFIGURACION DE LA SIMULACION
# ==============================================================================

DEFAULT_QUANTUM = 2         # Quantum por defecto para Round Robin
DEFAULT_SPEED = 1.0         # Velocidad de simulacion (1.0 = tiempo real)
MAX_PROCESSES = 20          # Limite de procesos en el sistema

# ==============================================================================
# CONFIGURACION DE LA INTERFAZ GRAFICA (PyGame)
# ==============================================================================

WINDOW_WIDTH = 1200         # Ancho de ventana en pixeles
WINDOW_HEIGHT = 800         # Alto de ventana en pixeles
FPS = 60                    # Frames por segundo

# ==============================================================================
# PALETA DE COLORES (RGB)
# ==============================================================================

COLORS = {
    # Fondos
    'background': (30, 30, 40),
    'panel': (45, 45, 60),
    'grid': (60, 60, 80),
    
    # Texto
    'text': (255, 255, 255),
    'text_dim': (150, 150, 150),
    
    # Estados y alertas
    'accent': (100, 200, 255),
    'success': (100, 255, 150),
    'warning': (255, 200, 100),
    'error': (255, 100, 100),
    
    # Estados de procesos
    'running': (100, 255, 150),
    'ready': (100, 200, 255),
    'waiting': (255, 200, 100),
    'completed': (150, 150, 150),
    'new': (255, 150, 255),
}

# Colores asignados a procesos para diferenciarlos en la visualizacion
PROCESS_COLORS = [
    (255, 107, 107),    # Rojo
    (78, 205, 196),     # Turquesa
    (255, 230, 109),    # Amarillo
    (170, 166, 255),    # Lavanda
    (255, 166, 158),    # Salmon
    (130, 204, 221),    # Celeste
    (255, 195, 160),    # Durazno
    (180, 255, 180),    # Verde claro
    (255, 180, 220),    # Rosa
    (200, 220, 255),    # Azul claro
    (255, 220, 180),    # Crema
    (180, 255, 220),    # Aqua
]

# ==============================================================================
# ALGORITMOS DISPONIBLES
# ==============================================================================

ALGORITHMS = {
    'FCFS': 'First Come First Served',
    'SJF': 'Shortest Job First',
    'PRIORITY': 'Priority Scheduling',
    'RR': 'Round Robin'
}

# ==============================================================================
# PROTOCOLO DE MENSAJES (Cliente-Servidor)
# ==============================================================================

MSG_TYPES = {
    # Operaciones de procesos
    'ADD_PROCESS': 'ADD',
    'REMOVE_PROCESS': 'REM',
    
    # Control de simulacion
    'START_SIM': 'START',
    'PAUSE_SIM': 'PAUSE',
    'RESET_SIM': 'RESET',
    
    # Configuracion
    'SET_ALGORITHM': 'ALGO',
    'SET_QUANTUM': 'QUANTUM',
    
    # Sincronizacion de estado
    'GET_STATE': 'STATE',
    'STATE_UPDATE': 'UPDATE',
    'TICK': 'TICK',
    
    # Respuestas
    'ACK': 'ACK',
    'ERROR': 'ERR',
    'DISCONNECT': 'BYE'
}
