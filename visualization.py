"""
visualization.py - Renderizado de la Interfaz Grafica

Modulo de visualizacion que utiliza PyGame para renderizar:
1. Panel de procesos con tabla de datos
2. Diagrama de Gantt en tiempo real
3. Visualizacion de CPU y cola Ready
4. Estadisticas de rendimiento
5. Controles e indicadores de estado

Layout de pantalla (1200x520):
+--------------------------------------------------+
| Header: Titulo + Estado + Tiempo                 |
+--------------------------------------------------+
| Algoritmos: [FCFS] [SJF] [PRIORITY] [RR]  Q=2    |
+--------------------------------------------------+
| Tabla Procesos    |    Gantt Chart               |
| (420x180)         |    (720x180)                 |
+--------------------------------------------------+
| CPU + Ready Queue |    Estadisticas              |
| (420x170)         |    (720x170)                 |
+--------------------------------------------------+
| Controles: [1-4] [SPACE] [A] [R] [+/-] [Q]       |
+--------------------------------------------------+

Autor: Julian Parra
Proyecto: Simulador de Scheduling de CPU
Materia: Sistemas Operativos - UABC 2025
"""

import pygame
import os

# Suprimir mensaje de bienvenida de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from typing import List, Dict, Optional, Tuple
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, COLORS, PROCESS_COLORS, 
    ALGORITHMS, FPS
)


class Renderer:
    """
    Clase principal de renderizado con PyGame.
    
    Responsabilidades:
    - Inicializar PyGame y crear ventana
    - Renderizar cada seccion de la interfaz
    - Manejar fuentes y colores
    - Controlar framerate
    
    El metodo render() es llamado cada frame por el cliente
    y recibe el estado actual del servidor.
    """
    
    def __init__(self, width: int = WINDOW_WIDTH, height: int = WINDOW_HEIGHT):
        """
        Inicializa PyGame y configura la ventana.
        
        Args:
            width:  Ancho de la ventana (default: 1200)
            height: Alto de la ventana (default: 520)
        """
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("Simulador de Scheduling - Sistemas Operativos")
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        
        # Sistema de fuentes con fallback
        self.font_title = pygame.font.SysFont('DejaVuSans', 28, bold=True)
        self.font_medium = pygame.font.SysFont('DejaVuSans', 18)
        self.font_small = pygame.font.SysFont('DejaVuSans', 14)
        self.font_tiny = pygame.font.SysFont('DejaVuSans', 12)
        
        # Estado local para rendering
        self.quantum = 2
        self._frame_count = 0
        
    def render(self, state: dict):
        """
        Renderiza un frame completo de la interfaz.
        
        Args:
            state: Estado de la simulacion desde el servidor
        """
        self._frame_count += 1
        
        # Limpiar pantalla
        self.screen.fill(COLORS['background'])
        
        # Renderizar cada seccion
        self._render_header(state)
        self._render_algorithm_selector(state)
        self._render_process_table(state)
        self._render_gantt_chart(state)
        self._render_cpu_visualization(state)
        self._render_statistics(state)
        self._render_controls_help()
        
        # Actualizar display y controlar FPS
        pygame.display.flip()
        self.clock.tick(FPS)
    
    def _render_header(self, state: dict):
        """
        Renderiza el encabezado con titulo y estado.
        
        Muestra:
        - Titulo del simulador (izquierda)
        - Estado actual: EJECUTANDO/PAUSADO/DETENIDO (derecha)
        - Tiempo de simulacion (derecha)
        """
        # Titulo principal
        title = self.font_title.render("Simulador de CPU Scheduling", True, COLORS['accent'])
        self.screen.blit(title, (20, 12))
        
        status_x = self.width - 180
        
        # Determinar estado y color
        if state.get('is_running'):
            if state.get('is_paused'):
                status = "PAUSADO"
                color = COLORS['warning']
            else:
                status = "EJECUTANDO"
                color = COLORS['success']
        else:
            status = "DETENIDO"
            color = COLORS['text_dim']
        
        # Panel de estado
        status_rect = pygame.Rect(status_x, 10, 160, 25)
        pygame.draw.rect(self.screen, COLORS['panel'], status_rect, border_radius=4)
        status_text = self.font_medium.render(status, True, color)
        status_text_rect = status_text.get_rect(center=status_rect.center)
        self.screen.blit(status_text, status_text_rect)
        
        # Tiempo actual
        time_text = self.font_medium.render(f"T = {state.get('current_time', 0)}", True, COLORS['text'])
        self.screen.blit(time_text, (status_x + 50, 40))
        
        # Separador horizontal
        pygame.draw.line(self.screen, COLORS['grid'], (20, 65), (self.width - 20, 65), 1)
    
    def _render_algorithm_selector(self, state: dict):
        """
        Renderiza los botones de seleccion de algoritmo.
        
        Los botones muestran:
        - Numero de tecla (1-4)
        - Nombre del algoritmo
        - Resaltado si esta seleccionado
        - Valor de quantum para Round Robin
        """
        y_start = 75
        
        # Mapeo de nombres para detectar algoritmo activo
        # El servidor puede enviar nombres largos o cortos
        algo_map = {
            'FCFS': ['FCFS', 'First Come First Served'],
            'SJF': ['SJF', 'Shortest Job First'],
            'PRIORITY': ['PRIORITY', 'Priority Scheduling', 'Priority'],
            'RR': ['RR', 'Round Robin']
        }
        
        algorithms = ['FCFS', 'SJF', 'PRIORITY', 'RR']
        x = 20
        
        current_algo = state.get('algorithm', 'FCFS')
        
        for i, algo in enumerate(algorithms):
            # Verificar si este algoritmo esta seleccionado
            is_selected = current_algo in algo_map[algo] or current_algo == algo
            
            btn_width = 90
            rect = pygame.Rect(x, y_start, btn_width, 28)
            
            if is_selected:
                # Boton activo: fondo de color accent
                pygame.draw.rect(self.screen, COLORS['accent'], rect, border_radius=4)
                text_color = COLORS['background']
            else:
                # Boton inactivo: fondo panel con borde
                pygame.draw.rect(self.screen, COLORS['panel'], rect, border_radius=4)
                pygame.draw.rect(self.screen, COLORS['grid'], rect, 1, border_radius=4)
                text_color = COLORS['text']
            
            # Texto: "N:ALGO"
            algo_text = self.font_small.render(f"{i+1}:{algo}", True, text_color)
            text_rect = algo_text.get_rect(center=rect.center)
            self.screen.blit(algo_text, text_rect)
            
            x += btn_width + 10
        
        # Indicador de quantum (resaltado solo para Round Robin)
        quantum_val = state.get('quantum', self.quantum)
        self.quantum = quantum_val
        
        is_rr = current_algo in algo_map['RR'] or current_algo == 'RR'
        quantum_color = COLORS['warning'] if is_rr else COLORS['text_dim']
        quantum_text = self.font_small.render(f"Q={quantum_val}", True, quantum_color)
        self.screen.blit(quantum_text, (x + 10, y_start + 5))
    
    def _render_process_table(self, state: dict):
        """
        Renderiza la tabla de procesos.
        
        Columnas:
        - Color: indicador visual del proceso
        - PID: identificador unico
        - Nombre: nombre del proceso (truncado a 6 chars)
        - Burst: tiempo total de CPU requerido
        - Llegada: tiempo de arrival
        - Prioridad: valor de prioridad
        - Restante: tiempo de CPU restante
        - Estado: NEW/READY/RUNNING/COMPLETED
        """
        y_start = 115
        table_height = 180
        table_width = 420
        
        # Panel contenedor
        panel_rect = pygame.Rect(20, y_start, table_width, table_height)
        pygame.draw.rect(self.screen, COLORS['panel'], panel_rect, border_radius=8)
        
        # Titulo de la tabla
        title = self.font_medium.render("Procesos", True, COLORS['text'])
        self.screen.blit(title, (30, y_start + 8))
        
        # Encabezados de columnas
        headers = ['', 'PID', 'Nombre', 'Burst', 'Lleg', 'Pri', 'Rest', 'Estado']
        header_widths = [12, 35, 65, 45, 40, 35, 40, 70]
        x = 30
        y = y_start + 35
        
        for header, width in zip(headers, header_widths):
            text = self.font_tiny.render(header, True, COLORS['text_dim'])
            self.screen.blit(text, (x, y))
            x += width
        
        # Linea separadora
        pygame.draw.line(self.screen, COLORS['grid'], (25, y + 15), (table_width + 15, y + 15), 1)
        
        # Filas de procesos
        processes = state.get('processes', [])
        y += 20
        max_visible = 6
        
        for i, proc in enumerate(processes[:max_visible]):
            x = 30
            color_idx = proc.get('color_index', i) % len(PROCESS_COLORS)
            proc_color = PROCESS_COLORS[color_idx]
            
            # Indicador circular de color
            pygame.draw.circle(self.screen, proc_color, (x + 5, y + 7), 4)
            x += 12
            
            # Preparar valores (truncar nombre y estado si necesario)
            name = proc.get('name', '')[:6]
            proc_state = proc.get('state', '')
            state_short = proc_state[:7] if len(proc_state) > 7 else proc_state
            
            values = [
                str(proc.get('pid', '')),
                name,
                str(proc.get('burst_time', '')),
                str(proc.get('arrival_time', '')),
                str(proc.get('priority', '')),
                str(proc.get('remaining_time', '')),
                state_short
            ]
            
            # Renderizar cada columna
            for j, (val, width) in enumerate(zip(values, header_widths[1:])):
                if j == 6:  # Columna de estado tiene colores especiales
                    state_colors = {
                        'RUNNING': COLORS['running'],
                        'READY': COLORS['ready'],
                        'COMPLET': COLORS['completed'],
                        'COMPLETED': COLORS['completed'],
                        'NEW': COLORS['new'],
                        'WAITING': COLORS['waiting']
                    }
                    text_color = state_colors.get(val, state_colors.get(proc_state, COLORS['text']))
                else:
                    text_color = COLORS['text']
                
                text = self.font_tiny.render(val, True, text_color)
                self.screen.blit(text, (x, y))
                x += width
            
            y += 22
        
        # Indicador de procesos adicionales
        if len(processes) > max_visible:
            more_text = self.font_tiny.render(f"+{len(processes) - max_visible} mas...", True, COLORS['text_dim'])
            self.screen.blit(more_text, (30, y))
    
    def _render_gantt_chart(self, state: dict):
        """
        Renderiza el diagrama de Gantt.
        
        El Gantt chart muestra la ejecucion de procesos en el tiempo:
        - Eje X: tiempo
        - Barras coloreadas: periodos de ejecucion
        - Gaps grises: CPU idle
        
        El chart auto-scroll muestra los ultimos 25 ticks si
        la simulacion es mas larga.
        """
        y_start = 115
        chart_width = 720
        chart_height = 180
        chart_x_start = 460
        
        # Panel contenedor
        panel_rect = pygame.Rect(chart_x_start, y_start, chart_width, chart_height)
        pygame.draw.rect(self.screen, COLORS['panel'], panel_rect, border_radius=8)
        
        # Titulo
        title = self.font_medium.render("Gantt Chart", True, COLORS['text'])
        self.screen.blit(title, (chart_x_start + 10, y_start + 8))
        
        gantt = state.get('gantt_chart', [])
        
        # Mensaje si no hay datos
        if not gantt:
            no_data = self.font_small.render("Agrega procesos e inicia la simulacion", True, COLORS['text_dim'])
            self.screen.blit(no_data, (chart_x_start + 180, y_start + 90))
            return
        
        # Dimensiones del area de grafico
        chart_x = chart_x_start + 20
        chart_y = y_start + 40
        chart_w = chart_width - 40
        chart_h = 80
        
        # Calcular escala de tiempo
        max_time = max(end for _, _, end in gantt)
        if max_time == 0:
            max_time = 1
        
        # Ventana visible: ultimos 25 ticks
        visible_time = min(max_time, 25)
        time_offset = max(0, max_time - visible_time)
        scale = chart_w / visible_time
        
        # Fondo del area de grafico
        pygame.draw.rect(self.screen, COLORS['background'], 
                        (chart_x, chart_y, chart_w, chart_h), border_radius=4)
        
        # Mapeo PID -> proceso para obtener colores
        processes = {p['pid']: p for p in state.get('processes', [])}
        
        # Renderizar barras de ejecucion
        for pid, start, end in gantt:
            # Convertir a coordenadas visibles
            vis_start = max(0, start - time_offset)
            vis_end = max(0, end - time_offset)
            
            if vis_end <= 0:
                continue
            
            x = chart_x + vis_start * scale
            w = (vis_end - vis_start) * scale
            
            # Determinar color y etiqueta
            if pid == -1:
                # CPU idle
                color = COLORS['grid']
                label = "-"
            else:
                proc = processes.get(pid, {})
                color_idx = proc.get('color_index', pid % len(PROCESS_COLORS))
                color = PROCESS_COLORS[color_idx]
                label = f"P{pid}"
            
            # Dibujar barra
            bar_rect = pygame.Rect(x + 1, chart_y + 10, max(w - 2, 2), chart_h - 20)
            pygame.draw.rect(self.screen, color, bar_rect, border_radius=2)
            
            # Etiqueta si hay espacio suficiente
            if w > 20:
                label_text = self.font_tiny.render(label, True, COLORS['background'])
                label_rect = label_text.get_rect(center=bar_rect.center)
                self.screen.blit(label_text, label_rect)
        
        # Linea de tiempo
        timeline_y = chart_y + chart_h + 5
        pygame.draw.line(self.screen, COLORS['text_dim'], 
                        (chart_x, timeline_y), (chart_x + chart_w, timeline_y), 1)
        
        # Marcas de tiempo
        step = max(1, visible_time // 10)
        for t in range(0, visible_time + 1, step):
            x = chart_x + t * scale
            pygame.draw.line(self.screen, COLORS['text_dim'], (x, timeline_y), (x, timeline_y + 5), 1)
            time_label = self.font_tiny.render(str(t + time_offset), True, COLORS['text_dim'])
            self.screen.blit(time_label, (x - 5, timeline_y + 8))
    
    def _render_cpu_visualization(self, state: dict):
        """
        Renderiza la visualizacion de CPU y cola Ready.
        
        Muestra:
        - CPU: proceso actual ejecutando o IDLE
        - Barra de progreso del proceso
        - Ready Queue: procesos esperando
        """
        y_start = 310
        panel_height = 170
        
        # Panel contenedor
        panel_rect = pygame.Rect(20, y_start, 420, panel_height)
        pygame.draw.rect(self.screen, COLORS['panel'], panel_rect, border_radius=8)
        
        # Titulo
        title = self.font_medium.render("CPU", True, COLORS['text'])
        self.screen.blit(title, (30, y_start + 8))
        
        # Dimensiones del bloque CPU
        cpu_x = 50
        cpu_y = y_start + 40
        cpu_w = 180
        cpu_h = 90
        
        running = state.get('running_process')
        
        if running:
            # CPU ejecutando un proceso
            proc = running
            color_idx = proc.get('color_index', 0) % len(PROCESS_COLORS)
            color = PROCESS_COLORS[color_idx]
            
            # Bloque CPU con color del proceso
            cpu_rect = pygame.Rect(cpu_x, cpu_y, cpu_w, cpu_h)
            pygame.draw.rect(self.screen, color, cpu_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLORS['text'], cpu_rect, 2, border_radius=8)
            
            # Nombre del proceso
            proc_name = proc.get('name', '')[:10]
            name_text = self.font_medium.render(f"P{proc.get('pid')}: {proc_name}", True, COLORS['background'])
            name_rect = name_text.get_rect(center=(cpu_x + cpu_w//2, cpu_y + 25))
            self.screen.blit(name_text, name_rect)
            
            # Calcular progreso
            remaining = proc.get('remaining_time', 0)
            burst = proc.get('burst_time', 1)
            progress = (burst - remaining) / burst if burst > 0 else 0
            
            # Barra de progreso
            prog_x = cpu_x + 15
            prog_y = cpu_y + 50
            prog_w = cpu_w - 30
            prog_h = 15
            
            pygame.draw.rect(self.screen, COLORS['background'], (prog_x, prog_y, prog_w, prog_h), border_radius=3)
            if progress > 0:
                pygame.draw.rect(self.screen, COLORS['success'], 
                               (prog_x, prog_y, int(prog_w * progress), prog_h), border_radius=3)
            
            # Texto de progreso
            prog_text = self.font_tiny.render(f"{int(progress*100)}% - {remaining}t restante", True, COLORS['background'])
            prog_rect = prog_text.get_rect(center=(cpu_x + cpu_w//2, cpu_y + 75))
            self.screen.blit(prog_text, prog_rect)
            
        else:
            # CPU idle
            cpu_rect = pygame.Rect(cpu_x, cpu_y, cpu_w, cpu_h)
            pygame.draw.rect(self.screen, COLORS['grid'], cpu_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLORS['text_dim'], cpu_rect, 2, border_radius=8)
            
            idle_text = self.font_medium.render("IDLE", True, COLORS['text_dim'])
            idle_rect = idle_text.get_rect(center=cpu_rect.center)
            self.screen.blit(idle_text, idle_rect)
        
        # Cola Ready
        ready_x = 260
        ready_label = self.font_small.render("Ready Queue", True, COLORS['text'])
        self.screen.blit(ready_label, (ready_x, y_start + 40))
        
        ready_procs = [p for p in state.get('processes', []) if p.get('state') == 'READY']
        y = y_start + 65
        max_visible = 4
        
        for proc in ready_procs[:max_visible]:
            color_idx = proc.get('color_index', 0) % len(PROCESS_COLORS)
            color = PROCESS_COLORS[color_idx]
            
            pygame.draw.rect(self.screen, color, (ready_x, y, 140, 20), border_radius=3)
            proc_text = self.font_tiny.render(f"P{proc.get('pid')} - {proc.get('name', '')[:8]}", True, COLORS['background'])
            self.screen.blit(proc_text, (ready_x + 8, y + 3))
            y += 25
        
        if len(ready_procs) > max_visible:
            more = self.font_tiny.render(f"+{len(ready_procs)-max_visible}", True, COLORS['text_dim'])
            self.screen.blit(more, (ready_x, y))
    
    def _render_statistics(self, state: dict):
        """
        Renderiza el panel de estadisticas.
        
        Metricas mostradas:
        - Avg Wait Time: tiempo promedio en cola READY
        - Avg Turnaround: tiempo promedio total en sistema
        - Avg Response: tiempo promedio hasta primera ejecucion
        - Throughput: procesos completados por unidad de tiempo
        - CPU Usage: porcentaje de utilizacion de CPU
        - Context Switches: numero de cambios de contexto
        - Completados: N/M procesos terminados
        """
        y_start = 310
        panel_height = 170
        panel_x = 460
        
        # Panel contenedor
        panel_rect = pygame.Rect(panel_x, y_start, 720, panel_height)
        pygame.draw.rect(self.screen, COLORS['panel'], panel_rect, border_radius=8)
        
        # Titulo
        title = self.font_medium.render("Estadisticas", True, COLORS['text'])
        self.screen.blit(title, (panel_x + 10, y_start + 8))
        
        stats = state.get('statistics', {})
        
        # Metricas en 2 columnas
        col1_metrics = [
            ("Avg Wait Time", f"{stats.get('avg_waiting_time', 0):.2f}"),
            ("Avg Turnaround", f"{stats.get('avg_turnaround_time', 0):.2f}"),
            ("Avg Response", f"{stats.get('avg_response_time', 0):.2f}"),
        ]
        
        col2_metrics = [
            ("Throughput", f"{stats.get('throughput', 0):.3f}"),
            ("CPU Usage", f"{stats.get('cpu_utilization', 0):.1f}%"),
            ("Ctx Switches", f"{state.get('context_switches', 0)}"),
        ]
        
        # Columna 1
        x1 = panel_x + 20
        y = y_start + 40
        for label, value in col1_metrics:
            label_text = self.font_small.render(label, True, COLORS['text_dim'])
            self.screen.blit(label_text, (x1, y))
            value_text = self.font_small.render(value, True, COLORS['accent'])
            self.screen.blit(value_text, (x1 + 120, y))
            y += 28
        
        # Columna 2
        x2 = panel_x + 260
        y = y_start + 40
        for label, value in col2_metrics:
            label_text = self.font_small.render(label, True, COLORS['text_dim'])
            self.screen.blit(label_text, (x2, y))
            value_text = self.font_small.render(value, True, COLORS['accent'])
            self.screen.blit(value_text, (x2 + 100, y))
            y += 28
        
        # Contador de completados
        completed = stats.get('completed_count', 0)
        total = stats.get('total_count', 0)
        comp_text = self.font_small.render(f"Completados: {completed}/{total}", True, COLORS['success'])
        self.screen.blit(comp_text, (x2, y + 10))
        
        # Barra vertical de CPU
        bar_x = panel_x + 500
        bar_y = y_start + 45
        bar_w = 180
        bar_h = 100
        
        cpu_util = stats.get('cpu_utilization', 0)
        
        # Fondo de la barra
        pygame.draw.rect(self.screen, COLORS['background'], (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        
        # Relleno segun utilizacion
        fill_h = int(bar_h * cpu_util / 100)
        if fill_h > 0:
            pygame.draw.rect(self.screen, COLORS['success'], 
                           (bar_x, bar_y + bar_h - fill_h, bar_w, fill_h), border_radius=5)
        
        # Etiqueta centrada
        cpu_label = self.font_small.render("CPU", True, COLORS['text'])
        cpu_label_rect = cpu_label.get_rect(center=(bar_x + bar_w//2, bar_y + bar_h//2 - 10))
        self.screen.blit(cpu_label, cpu_label_rect)
        
        cpu_val = self.font_medium.render(f"{cpu_util:.0f}%", True, COLORS['text'])
        cpu_val_rect = cpu_val.get_rect(center=(bar_x + bar_w//2, bar_y + bar_h//2 + 12))
        self.screen.blit(cpu_val, cpu_val_rect)
    
    def _render_controls_help(self):
        """Renderiza la barra de ayuda de controles."""
        y = self.height - 45
        
        # Panel de fondo
        help_rect = pygame.Rect(20, y, self.width - 40, 35)
        pygame.draw.rect(self.screen, COLORS['panel'], help_rect, border_radius=6)
        
        # Texto de controles
        controls = "[1-4] Algoritmo    [SPACE] Play/Pause    [A] Agregar    [R] Reset    [+/-] Quantum    [Q] Salir"
        
        text = self.font_small.render(controls, True, COLORS['text_dim'])
        text_rect = text.get_rect(center=help_rect.center)
        self.screen.blit(text, text_rect)
    
    def get_events(self) -> List[pygame.event.Event]:
        """Retorna la lista de eventos de PyGame pendientes."""
        return pygame.event.get()
    
    def quit(self):
        """Cierra PyGame y libera recursos."""
        pygame.quit()
