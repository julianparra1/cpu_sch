"""
protocol.py - Protocolo de Comunicacion Cliente-Servidor

Este modulo define el protocolo de mensajes usado para la comunicacion
entre el servidor y los clientes via sockets TCP. Utiliza JSON como
formato de serializacion con un delimitador de linea para separar mensajes.

Formato de mensaje:
    {"type": "MSG_TYPE", "data": {...}, "client_id": "optional"}\n

El delimitador \n permite manejar mensajes parciales cuando se reciben
datos fragmentados por el protocolo TCP.

Autor: Julian Parra
Proyecto: Simulador de Scheduling de CPU
Materia: Sistemas Operativos - UABC 2025
"""

import json
from typing import Any, Optional
from config import MSG_TYPES


class Message:
    """
    Representa un mensaje del protocolo de comunicacion.
    
    Attributes:
        type:      Tipo de mensaje (ADD, START, UPDATE, etc.)
        data:      Payload del mensaje (diccionario con datos)
        client_id: Identificador del cliente (opcional)
    """
    
    def __init__(self, msg_type: str, data: Any = None, client_id: Optional[str] = None):
        self.type = msg_type
        self.data = data
        self.client_id = client_id
    
    def to_json(self) -> str:
        """Serializa el mensaje a string JSON."""
        return json.dumps({
            'type': self.type,
            'data': self.data,
            'client_id': self.client_id
        })
    
    def to_bytes(self) -> bytes:
        """
        Convierte el mensaje a bytes para transmision por socket.
        Agrega \n como delimitador para separar mensajes consecutivos.
        """
        return (self.to_json() + '\n').encode('utf-8')
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserializa un mensaje desde string JSON."""
        try:
            data = json.loads(json_str)
            return cls(
                msg_type=data.get('type', ''),
                data=data.get('data'),
                client_id=data.get('client_id')
            )
        except json.JSONDecodeError:
            return cls(msg_type=MSG_TYPES['ERROR'], data='Invalid JSON')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Message':
        """Crea un mensaje desde bytes recibidos del socket."""
        return cls.from_json(data.decode('utf-8').strip())
    
    def __str__(self):
        return f"Message({self.type}, {self.data})"


class Protocol:
    """
    Factory de mensajes del protocolo.
    
    Provee metodos estaticos para crear cada tipo de mensaje,
    asegurando el formato correcto y simplificando el codigo
    del cliente y servidor.
    """
    
    @staticmethod
    def add_process(name: str, burst_time: int, arrival_time: int = 0, priority: int = 5) -> Message:
        """Crea mensaje para agregar un nuevo proceso al sistema."""
        return Message(MSG_TYPES['ADD_PROCESS'], {
            'name': name,
            'burst_time': burst_time,
            'arrival_time': arrival_time,
            'priority': priority
        })
    
    @staticmethod
    def remove_process(pid: int) -> Message:
        """Crea mensaje para eliminar un proceso por su PID."""
        return Message(MSG_TYPES['REMOVE_PROCESS'], {'pid': pid})
    
    @staticmethod
    def start_simulation() -> Message:
        """Crea mensaje para iniciar la simulacion."""
        return Message(MSG_TYPES['START_SIM'])
    
    @staticmethod
    def pause_simulation() -> Message:
        """Crea mensaje para pausar/reanudar la simulacion."""
        return Message(MSG_TYPES['PAUSE_SIM'])
    
    @staticmethod
    def reset_simulation() -> Message:
        """Crea mensaje para reiniciar la simulacion a tiempo 0."""
        return Message(MSG_TYPES['RESET_SIM'])
    
    @staticmethod
    def set_algorithm(algorithm: str) -> Message:
        """Crea mensaje para cambiar el algoritmo de scheduling."""
        return Message(MSG_TYPES['SET_ALGORITHM'], {'algorithm': algorithm})
    
    @staticmethod
    def set_quantum(quantum: int) -> Message:
        """Crea mensaje para establecer el quantum de Round Robin."""
        return Message(MSG_TYPES['SET_QUANTUM'], {'quantum': quantum})
    
    @staticmethod
    def get_state() -> Message:
        """Crea mensaje para solicitar el estado actual."""
        return Message(MSG_TYPES['GET_STATE'])
    
    @staticmethod
    def state_update(state: dict) -> Message:
        """Crea mensaje con el estado completo de la simulacion."""
        return Message(MSG_TYPES['STATE_UPDATE'], state)
    
    @staticmethod
    def tick() -> Message:
        """Crea mensaje para avanzar un tick manual."""
        return Message(MSG_TYPES['TICK'])
    
    @staticmethod
    def ack(data: Any = None) -> Message:
        """Crea mensaje de confirmacion."""
        return Message(MSG_TYPES['ACK'], data)
    
    @staticmethod
    def error(error_msg: str) -> Message:
        """Crea mensaje de error."""
        return Message(MSG_TYPES['ERROR'], error_msg)
    
    @staticmethod
    def disconnect() -> Message:
        """Crea mensaje de desconexion."""
        return Message(MSG_TYPES['DISCONNECT'])


class MessageBuffer:
    """
    Buffer para manejar mensajes parciales en comunicacion TCP.
    
    TCP es un protocolo de stream, no de mensajes. Esto significa que
    los datos pueden llegar fragmentados o multiples mensajes pueden
    llegar juntos en una sola lectura. Este buffer acumula los datos
    recibidos y extrae mensajes completos (delimitados por \n).
    
    Ejemplo de uso:
        buffer = MessageBuffer()
        # En el loop de recepcion:
        data = socket.recv(4096)
        messages = buffer.add_data(data)
        for msg in messages:
            process(msg)
    """
    
    def __init__(self):
        self.buffer = ""
    
    def add_data(self, data: bytes) -> list[Message]:
        """
        Agrega datos al buffer y extrae mensajes completos.
        
        Args:
            data: Bytes recibidos del socket
            
        Returns:
            Lista de mensajes completos encontrados
        """
        self.buffer += data.decode('utf-8')
        messages = []
        
        # Extraer mensajes completos (terminados en \n)
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            if line.strip():
                try:
                    messages.append(Message.from_json(line))
                except Exception:
                    pass
        
        return messages
    
    def clear(self):
        """Limpia el buffer descartando datos pendientes."""
        self.buffer = ""
