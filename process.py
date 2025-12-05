"""
process.py - Modelo de Proceso para el Simulador de Scheduling

Este modulo define la estructura de datos Process que representa un proceso
en el sistema operativo simulado. Incluye todos los atributos necesarios
para los algoritmos de scheduling y el calculo de metricas.

Modelo de estados de un proceso:
    NEW -> READY -> RUNNING -> COMPLETED
                 \-> WAITING -/

Autor: Julian Parra
Proyecto: Simulador de Scheduling de CPU
Materia: Sistemas Operativos - UABC 2025
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProcessState(Enum):
    """
    Estados posibles de un proceso en el sistema.
    
    NEW:       Proceso recien creado, aun no admitido
    READY:     En cola, esperando CPU
    RUNNING:   Actualmente ejecutandose en CPU
    WAITING:   Bloqueado esperando I/O (no usado en esta simulacion)
    COMPLETED: Termino su ejecucion
    """
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"


@dataclass
class Process:
    """
    Representa un proceso en el simulador de scheduling.
    
    Atributos principales:
        pid:            Identificador unico del proceso
        name:           Nombre descriptivo (ej: "Chrome", "Python")
        burst_time:     Tiempo total de CPU requerido (unidades de tiempo)
        arrival_time:   Momento en que el proceso llega al sistema
        priority:       Nivel de prioridad (1=alta, 10=baja)
    
    Atributos de ejecucion (calculados dinamicamente):
        remaining_time:   CPU restante por ejecutar
        state:            Estado actual del proceso
        start_time:       Cuando comenzo a ejecutarse por primera vez
        completion_time:  Cuando termino completamente
    
    Metricas de rendimiento:
        waiting_time:     Tiempo total en cola READY
        turnaround_time:  Tiempo total desde llegada hasta completar
        response_time:    Tiempo desde llegada hasta primera ejecucion
    """
    pid: int
    name: str
    burst_time: int
    arrival_time: int = 0
    priority: int = 5
    remaining_time: int = field(init=False)
    state: ProcessState = ProcessState.NEW
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    waiting_time: int = 0
    turnaround_time: int = 0
    response_time: Optional[int] = None
    color_index: int = 0
    execution_history: list = field(default_factory=list)
    
    def __post_init__(self):
        """Inicializa remaining_time igual a burst_time al crear el proceso."""
        self.remaining_time = self.burst_time
    
    def execute(self, time_units: int, current_time: int) -> int:
        """
        Ejecuta el proceso por un numero de unidades de tiempo.
        
        Este metodo simula la ejecucion del proceso en la CPU:
        1. Cambia el estado a RUNNING si no lo esta
        2. Registra el tiempo de primera ejecucion (response time)
        3. Decrementa el tiempo restante
        4. Marca como COMPLETED si termino
        
        Args:
            time_units:   Unidades de tiempo a ejecutar (quantum o hasta terminar)
            current_time: Tiempo actual del reloj del sistema
            
        Returns:
            Unidades de tiempo realmente ejecutadas (puede ser menor si el
            proceso termina antes de agotar el time_units dado)
        """
        if self.state != ProcessState.RUNNING:
            self.state = ProcessState.RUNNING
        
        # Primera vez que ejecuta: registrar response time
        if self.start_time is None:
            self.start_time = current_time
            self.response_time = current_time - self.arrival_time
        
        # Ejecutar el minimo entre lo solicitado y lo que queda
        actual_execution = min(time_units, self.remaining_time)
        self.remaining_time -= actual_execution
        
        # Registrar en historial para el diagrama de Gantt
        self.execution_history.append({
            'start': current_time,
            'end': current_time + actual_execution,
            'duration': actual_execution
        })
        
        # Verificar si el proceso termino
        if self.remaining_time <= 0:
            self.state = ProcessState.COMPLETED
            self.completion_time = current_time + actual_execution
            self.turnaround_time = self.completion_time - self.arrival_time
        
        return actual_execution
    
    def preempt(self):
        """
        Interrumpe el proceso actual (preemption).
        
        Usado por algoritmos preemptivos como Round Robin cuando
        el quantum expira, o Priority Scheduling cuando llega un
        proceso de mayor prioridad.
        """
        if self.state == ProcessState.RUNNING:
            self.state = ProcessState.READY
    
    def calculate_waiting_time(self):
        """
        Calcula el tiempo de espera basado en el historial de ejecucion.
        
        Waiting Time = Turnaround Time - Burst Time
        Es decir, el tiempo que paso en estado READY esperando CPU.
        """
        if self.completion_time is not None:
            total_execution = sum(h['duration'] for h in self.execution_history)
            self.waiting_time = self.turnaround_time - total_execution
    
    def reset(self):
        """Reinicia el proceso a su estado inicial para re-simular."""
        self.remaining_time = self.burst_time
        self.state = ProcessState.NEW
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = None
        self.execution_history = []
    
    def to_dict(self) -> dict:
        """
        Serializa el proceso a diccionario para transmision por socket.
        El servidor usa esto para enviar el estado a los clientes.
        """
        return {
            'pid': self.pid,
            'name': self.name,
            'burst_time': self.burst_time,
            'arrival_time': self.arrival_time,
            'priority': self.priority,
            'remaining_time': self.remaining_time,
            'state': self.state.value,
            'start_time': self.start_time,
            'completion_time': self.completion_time,
            'waiting_time': self.waiting_time,
            'turnaround_time': self.turnaround_time,
            'response_time': self.response_time,
            'color_index': self.color_index,
            'execution_history': self.execution_history
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Process':
        """Crea un proceso desde un diccionario (deserializacion)."""
        process = cls(
            pid=data['pid'],
            name=data['name'],
            burst_time=data['burst_time'],
            arrival_time=data.get('arrival_time', 0),
            priority=data.get('priority', 5),
            color_index=data.get('color_index', 0)
        )
        process.remaining_time = data.get('remaining_time', process.burst_time)
        process.state = ProcessState(data.get('state', 'NEW'))
        process.start_time = data.get('start_time')
        process.completion_time = data.get('completion_time')
        process.waiting_time = data.get('waiting_time', 0)
        process.turnaround_time = data.get('turnaround_time', 0)
        process.response_time = data.get('response_time')
        process.execution_history = data.get('execution_history', [])
        return process
    
    def __str__(self):
        return f"Process({self.pid}, {self.name}, burst={self.burst_time}, state={self.state.value})"
    
    def __repr__(self):
        return self.__str__()


class ProcessQueue:
    """
    Cola de procesos con operaciones para scheduling.
    
    Mantiene la lista de todos los procesos en el sistema y provee
    metodos para filtrarlos por estado, lo cual es necesario para
    los algoritmos de scheduling.
    """
    
    def __init__(self):
        self.processes: list[Process] = []
    
    def add(self, process: Process):
        """Agrega un proceso al sistema."""
        self.processes.append(process)
    
    def remove(self, pid: int) -> Optional[Process]:
        """Remueve y retorna un proceso por su PID."""
        for i, p in enumerate(self.processes):
            if p.pid == pid:
                return self.processes.pop(i)
        return None
    
    def get_ready_processes(self, current_time: int) -> list[Process]:
        """
        Obtiene procesos que pueden ejecutarse en el tiempo actual.
        
        Un proceso esta listo si:
        1. Su arrival_time <= current_time (ya llego)
        2. Esta en estado NEW o READY (no completado ni ejecutando)
        """
        return [p for p in self.processes 
                if p.arrival_time <= current_time 
                and p.state in (ProcessState.NEW, ProcessState.READY)]
    
    def get_completed_processes(self) -> list[Process]:
        """Retorna lista de procesos que ya terminaron."""
        return [p for p in self.processes if p.state == ProcessState.COMPLETED]
    
    def get_running_process(self) -> Optional[Process]:
        """Retorna el proceso actualmente en CPU, o None."""
        for p in self.processes:
            if p.state == ProcessState.RUNNING:
                return p
        return None
    
    def all_completed(self) -> bool:
        """Verifica si todos los procesos han terminado."""
        if not self.processes:
            return False
        return all(p.state == ProcessState.COMPLETED for p in self.processes)
    
    def reset_all(self):
        """Reinicia todos los procesos a su estado inicial."""
        for p in self.processes:
            p.reset()
    
    def clear(self):
        """Elimina todos los procesos de la cola."""
        self.processes.clear()
    
    def __len__(self):
        return len(self.processes)
    
    def __iter__(self):
        return iter(self.processes)
