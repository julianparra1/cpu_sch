"""
scheduling_algorithms.py - Implementacion de Algoritmos de Scheduling

Este modulo implementa los algoritmos clasicos de calendarizacion de CPU:

1. FCFS (First Come First Served)
   - No preemptivo
   - Orden de llegada
   - Simple pero puede causar convoy effect

2. SJF (Shortest Job First)
   - No preemptivo
   - Proceso mas corto primero
   - Optimo para minimizar tiempo de espera promedio

3. SRTF (Shortest Remaining Time First)
   - Version preemptiva de SJF
   - Proceso con menor tiempo restante primero

4. Priority Scheduling
   - No preemptivo
   - Mayor prioridad (numero menor) primero
   - Puede causar starvation

5. Round Robin
   - Preemptivo con quantum fijo
   - Rotacion circular de procesos
   - Mas justo, mayor overhead

Autor: Julian Parra
Proyecto: Simulador de Scheduling de CPU
Materia: Sistemas Operativos - UABC 2025
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from process import Process, ProcessState, ProcessQueue
from config import DEFAULT_QUANTUM


class SchedulingAlgorithm(ABC):
    """
    Clase base abstracta para algoritmos de scheduling.
    
    Define la interfaz que todos los algoritmos deben implementar:
    - select_next(): Selecciona el proximo proceso a ejecutar
    - get_time_slice(): Determina cuanto tiempo ejecutara
    - is_preemptive(): Indica si el algoritmo puede interrumpir procesos
    """
    
    def __init__(self):
        self.name = "Base"
        self.description = "Algoritmo base"
    
    @abstractmethod
    def select_next(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        """
        Selecciona el proximo proceso a ejecutar de la cola ready.
        
        Args:
            ready_queue:  Lista de procesos en estado READY
            current_time: Tiempo actual del sistema
            
        Returns:
            Proceso seleccionado o None si la cola esta vacia
        """
        pass
    
    @abstractmethod
    def get_time_slice(self, process: Process) -> int:
        """
        Determina cuantas unidades de tiempo ejecutara el proceso.
        
        Para algoritmos no preemptivos: retorna remaining_time (ejecuta hasta terminar)
        Para Round Robin: retorna el quantum configurado
        
        Args:
            process: Proceso que va a ejecutar
            
        Returns:
            Unidades de tiempo a ejecutar
        """
        pass
    
    def is_preemptive(self) -> bool:
        """Indica si el algoritmo puede interrumpir un proceso en ejecucion."""
        return False


class FCFSScheduler(SchedulingAlgorithm):
    """
    First Come First Served (FCFS)
    
    El algoritmo mas simple: ejecuta los procesos en el orden en que llegan.
    No es preemptivo, un proceso ocupa la CPU hasta terminar.
    
    Ventajas:
    - Facil de implementar y entender
    - Sin overhead de context switch innecesario
    
    Desventajas:
    - Convoy effect: procesos cortos esperan a procesos largos
    - Tiempo de espera promedio alto
    """
    
    def __init__(self):
        super().__init__()
        self.name = "FCFS"
        self.description = "First Come First Served - Procesos se ejecutan en orden de llegada"
    
    def select_next(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            return None
        # Ordenar por tiempo de llegada, desempatar por PID
        sorted_queue = sorted(ready_queue, key=lambda p: (p.arrival_time, p.pid))
        return sorted_queue[0]
    
    def get_time_slice(self, process: Process) -> int:
        return process.remaining_time


class SJFScheduler(SchedulingAlgorithm):
    """
    Shortest Job First (SJF)
    
    Selecciona el proceso con menor burst time. Es optimo para minimizar
    el tiempo de espera promedio, pero requiere conocer el burst time
    de antemano (en la practica se estima).
    
    Ventajas:
    - Minimiza tiempo de espera promedio
    - Buen throughput
    
    Desventajas:
    - Requiere conocer burst time (predecir en sistemas reales)
    - Puede causar starvation de procesos largos
    """
    
    def __init__(self):
        super().__init__()
        self.name = "SJF"
        self.description = "Shortest Job First - Proceso mas corto se ejecuta primero"
    
    def select_next(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            return None
        # Ordenar por remaining_time para manejar procesos parcialmente ejecutados
        sorted_queue = sorted(ready_queue, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))
        return sorted_queue[0]
    
    def get_time_slice(self, process: Process) -> int:
        return process.remaining_time


class SRTFScheduler(SchedulingAlgorithm):
    """
    Shortest Remaining Time First (SRTF)
    
    Version preemptiva de SJF. Si llega un proceso con menor remaining_time
    que el proceso actual, se hace preemption.
    
    Para simular preemption, ejecutamos solo 1 unidad de tiempo por tick
    y re-evaluamos la cola en cada tick.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "SRTF"
        self.description = "Shortest Remaining Time First - Version preemptiva de SJF"
    
    def select_next(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            return None
        sorted_queue = sorted(ready_queue, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))
        return sorted_queue[0]
    
    def get_time_slice(self, process: Process) -> int:
        # Ejecutar solo 1 unidad para permitir preemption en cada tick
        return 1
    
    def is_preemptive(self) -> bool:
        return True


class PriorityScheduler(SchedulingAlgorithm):
    """
    Priority Scheduling
    
    Cada proceso tiene una prioridad asignada. El proceso con mayor
    prioridad (menor numero en nuestra convencion) se ejecuta primero.
    
    Convencion: prioridad 1 = maxima, prioridad 10 = minima
    
    Ventajas:
    - Permite diferenciar procesos importantes
    
    Desventajas:
    - Starvation: procesos de baja prioridad pueden nunca ejecutarse
    - Solucion: aging (incrementar prioridad con el tiempo)
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Priority"
        self.description = "Priority Scheduling - Proceso con mayor prioridad se ejecuta primero"
    
    def select_next(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            return None
        # Menor numero = mayor prioridad
        sorted_queue = sorted(ready_queue, key=lambda p: (p.priority, p.arrival_time, p.pid))
        return sorted_queue[0]
    
    def get_time_slice(self, process: Process) -> int:
        return process.remaining_time


class RoundRobinScheduler(SchedulingAlgorithm):
    """
    Round Robin (RR)
    
    Cada proceso ejecuta por un quantum de tiempo fijo. Al expirar el
    quantum, el proceso vuelve al final de la cola y el siguiente ejecuta.
    
    Es el algoritmo mas usado en sistemas de tiempo compartido por su
    justicia: todos los procesos reciben CPU regularmente.
    
    Ventajas:
    - Justo: ningun proceso monopoliza la CPU
    - Buen tiempo de respuesta para procesos interactivos
    
    Desventajas:
    - Overhead por context switches frecuentes
    - Tiempo de espera puede ser alto si quantum es muy pequeno
    
    Seleccion de quantum:
    - Muy pequeno: demasiados context switches
    - Muy grande: comportamiento similar a FCFS
    - Regla practica: 80% de procesos deben terminar en un quantum
    """
    
    def __init__(self, quantum: int = DEFAULT_QUANTUM):
        super().__init__()
        self.name = "Round Robin"
        self.description = f"Round Robin - Cada proceso ejecuta por {quantum} unidades de tiempo"
        self.quantum = quantum
        self._current_index = 0
        self._last_process_pid = None
    
    def set_quantum(self, quantum: int):
        """Actualiza el valor del quantum."""
        self.quantum = quantum
        self.description = f"Round Robin - Cada proceso ejecuta por {quantum} unidades de tiempo"
    
    def select_next(self, ready_queue: List[Process], current_time: int) -> Optional[Process]:
        if not ready_queue:
            self._current_index = 0
            return None
        
        # Mantener orden de llegada para rotacion justa
        sorted_queue = sorted(ready_queue, key=lambda p: (p.arrival_time, p.pid))
        
        # Rotar al siguiente proceso despues de preemption
        if self._last_process_pid is not None:
            try:
                last_idx = next(i for i, p in enumerate(sorted_queue) 
                               if p.pid == self._last_process_pid)
                self._current_index = (last_idx + 1) % len(sorted_queue)
            except StopIteration:
                self._current_index = 0
        
        if self._current_index >= len(sorted_queue):
            self._current_index = 0
        
        selected = sorted_queue[self._current_index]
        self._last_process_pid = selected.pid
        return selected
    
    def get_time_slice(self, process: Process) -> int:
        # Ejecutar quantum o lo que reste, lo que sea menor
        return min(self.quantum, process.remaining_time)
    
    def is_preemptive(self) -> bool:
        return True
    
    def reset(self):
        """Reinicia el estado interno del scheduler."""
        self._current_index = 0
        self._last_process_pid = None


class SchedulerManager:
    """
    Manejador principal del sistema de scheduling.
    
    Esta clase coordina la ejecucion de la simulacion:
    1. Mantiene la cola de procesos
    2. Aplica el algoritmo de scheduling seleccionado
    3. Ejecuta los procesos tick por tick
    4. Registra el diagrama de Gantt
    5. Calcula estadisticas de rendimiento
    
    El servidor crea una instancia de SchedulerManager y llama a tick()
    periodicamente para avanzar la simulacion.
    """
    
    def __init__(self):
        # Algoritmos disponibles
        self.algorithms = {
            'FCFS': FCFSScheduler(),
            'SJF': SJFScheduler(),
            'SRTF': SRTFScheduler(),
            'PRIORITY': PriorityScheduler(),
            'RR': RoundRobinScheduler()
        }
        self.current_algorithm = self.algorithms['FCFS']
        
        # Estado de la simulacion
        self.process_queue = ProcessQueue()
        self.current_time = 0
        self.running_process: Optional[Process] = None
        self.time_slice_remaining = 0
        
        # Gantt chart: lista de tuplas (pid, start_time, end_time)
        # pid=-1 indica CPU idle
        self.gantt_chart: List[Tuple[int, int, int]] = []
        
        # Control de simulacion
        self.is_running = False
        self.is_paused = False
        self._context_switches = 0
    
    def set_algorithm(self, algorithm_name: str) -> bool:
        """Cambia el algoritmo de scheduling activo."""
        if algorithm_name in self.algorithms:
            self.current_algorithm = self.algorithms[algorithm_name]
            if isinstance(self.current_algorithm, RoundRobinScheduler):
                self.current_algorithm.reset()
            return True
        return False
    
    def set_quantum(self, quantum: int):
        """Configura el quantum para Round Robin."""
        if 'RR' in self.algorithms:
            self.algorithms['RR'].set_quantum(quantum)
    
    def add_process(self, process: Process):
        """Agrega un proceso al sistema con un color unico asignado."""
        process.color_index = len(self.process_queue) % 12
        self.process_queue.add(process)
    
    def remove_process(self, pid: int) -> bool:
        """Elimina un proceso del sistema."""
        return self.process_queue.remove(pid) is not None
    
    def start(self):
        """Inicia la simulacion."""
        self.is_running = True
        self.is_paused = False
    
    def pause(self):
        """Pausa la simulacion."""
        self.is_paused = True
    
    def resume(self):
        """Reanuda la simulacion pausada."""
        self.is_paused = False
    
    def reset(self):
        """Reinicia la simulacion a tiempo 0."""
        self.current_time = 0
        self.running_process = None
        self.time_slice_remaining = 0
        self.gantt_chart.clear()
        self.is_running = False
        self.is_paused = False
        self._context_switches = 0
        self.process_queue.reset_all()
        if isinstance(self.current_algorithm, RoundRobinScheduler):
            self.current_algorithm.reset()
    
    def tick(self) -> dict:
        """
        Ejecuta un tick de la simulacion (1 unidad de tiempo).
        
        Logica principal:
        1. Verificar si la simulacion esta activa
        2. Obtener procesos listos en el tiempo actual
        3. Manejar preemption si el algoritmo lo requiere
        4. Seleccionar proceso si la CPU esta libre
        5. Ejecutar proceso actual
        6. Actualizar Gantt chart
        7. Incrementar tiempo
        
        Returns:
            Estado actual de la simulacion
        """
        if not self.is_running or self.is_paused:
            return self.get_state()
        
        # Terminar si todos los procesos completaron
        if self.process_queue.all_completed():
            self.is_running = False
            return self.get_state()
        
        # Obtener procesos que ya llegaron y estan listos
        ready_queue = self.process_queue.get_ready_processes(self.current_time)
        
        # Transicionar procesos NEW a READY
        for p in ready_queue:
            if p.state == ProcessState.NEW:
                p.state = ProcessState.READY
        
        # Manejar preemption para algoritmos preemptivos
        if self.running_process and self.current_algorithm.is_preemptive():
            if self.time_slice_remaining <= 0:
                self.running_process.preempt()
                self._context_switches += 1
                self.running_process = None
        
        # Seleccionar proceso si CPU esta libre
        if self.running_process is None:
            ready_for_exec = [p for p in ready_queue if p.state == ProcessState.READY]
            if ready_for_exec:
                self.running_process = self.current_algorithm.select_next(
                    ready_for_exec, self.current_time)
                if self.running_process:
                    self.time_slice_remaining = self.current_algorithm.get_time_slice(
                        self.running_process)
                    if self.running_process.state != ProcessState.RUNNING:
                        self._context_switches += 1
        
        # Ejecutar proceso actual
        if self.running_process:
            executed = self.running_process.execute(1, self.current_time)
            self.time_slice_remaining -= executed
            
            # Actualizar Gantt chart
            if self.gantt_chart and self.gantt_chart[-1][0] == self.running_process.pid:
                # Extender entrada existente
                old = self.gantt_chart[-1]
                self.gantt_chart[-1] = (old[0], old[1], self.current_time + executed)
            else:
                # Nueva entrada
                self.gantt_chart.append((
                    self.running_process.pid, 
                    self.current_time, 
                    self.current_time + executed
                ))
            
            # Proceso termino
            if self.running_process.state == ProcessState.COMPLETED:
                self.running_process.calculate_waiting_time()
                self.running_process = None
        else:
            # CPU idle - registrar en Gantt
            if not self.gantt_chart or self.gantt_chart[-1][0] != -1:
                self.gantt_chart.append((-1, self.current_time, self.current_time + 1))
            else:
                old = self.gantt_chart[-1]
                self.gantt_chart[-1] = (old[0], old[1], self.current_time + 1)
        
        # Incrementar waiting_time para procesos en READY
        for p in ready_queue:
            if p.state == ProcessState.READY and p != self.running_process:
                p.waiting_time += 1
        
        self.current_time += 1
        return self.get_state()
    
    def get_state(self) -> dict:
        """Retorna el estado completo de la simulacion para enviar a clientes."""
        return {
            'current_time': self.current_time,
            'algorithm': self.current_algorithm.name,
            'algorithm_desc': self.current_algorithm.description,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'running_process': self.running_process.to_dict() if self.running_process else None,
            'processes': [p.to_dict() for p in self.process_queue.processes],
            'gantt_chart': self.gantt_chart,
            'statistics': self.get_statistics(),
            'context_switches': self._context_switches
        }
    
    def get_statistics(self) -> dict:
        """
        Calcula metricas de rendimiento de la simulacion.
        
        Metricas calculadas:
        - Avg Waiting Time:    Promedio de tiempo en cola READY
        - Avg Turnaround Time: Promedio de tiempo total en sistema
        - Avg Response Time:   Promedio de tiempo hasta primera ejecucion
        - Throughput:          Procesos completados por unidad de tiempo
        - CPU Utilization:     Porcentaje de tiempo que CPU estuvo ocupada
        """
        completed = self.process_queue.get_completed_processes()
        
        if not completed:
            return {
                'avg_waiting_time': 0,
                'avg_turnaround_time': 0,
                'avg_response_time': 0,
                'throughput': 0,
                'cpu_utilization': 0,
                'completed_count': 0,
                'total_count': len(self.process_queue)
            }
        
        total_waiting = sum(p.waiting_time for p in completed)
        total_turnaround = sum(p.turnaround_time for p in completed)
        total_response = sum(p.response_time or 0 for p in completed)
        
        # CPU utilization = tiempo ejecutando / tiempo total
        total_burst = sum(p.burst_time for p in self.process_queue.processes)
        cpu_util = (total_burst / self.current_time * 100) if self.current_time > 0 else 0
        
        return {
            'avg_waiting_time': total_waiting / len(completed),
            'avg_turnaround_time': total_turnaround / len(completed),
            'avg_response_time': total_response / len(completed),
            'throughput': len(completed) / self.current_time if self.current_time > 0 else 0,
            'cpu_utilization': min(cpu_util, 100),
            'completed_count': len(completed),
            'total_count': len(self.process_queue)
        }
