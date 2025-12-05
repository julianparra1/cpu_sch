# 🖥️ Simulador Visual de Algoritmos de Calendarización de Procesos

## Proyecto Final - Sistemas Operativos

Este proyecto implementa un **simulador visual interactivo** de algoritmos de calendarización de procesos (CPU Scheduling) utilizando comunicación por sockets (IPC) entre un servidor y múltiples clientes.


```bash
# Instalar dependencias
pip install pygame

# O usar el archivo de requirements
pip install -r requirements.txt
```

## Uso

### Iniciar el Servidor (Terminal 1)
```bash
python server.py
```

### Iniciar el Cliente Visual (Terminal 2)
```bash
python client.py
```

### Iniciar Cliente Adicional para agregar procesos (Terminal 3, opcional)
```bash
python process_generator.py
```

```
┌─────────────────┐     Socket TCP     ┌─────────────────┐
│  Client GUI     │◄──────────────────►│     Server      │
│  (PyGame)       │                    │  (Scheduling)   │
└─────────────────┘                    └─────────────────┘
                                              ▲
┌─────────────────┐     Socket TCP           │
│ Process         │◄─────────────────────────┘
│ Generator       │
└─────────────────┘
```
