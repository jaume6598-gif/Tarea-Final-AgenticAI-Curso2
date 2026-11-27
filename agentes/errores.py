"""Errores controlados de los flujos.

Cada error lleva un codigo HTTP y un mensaje claro para el usuario.
El detalle tecnico queda solo en el log.
"""


class ErrorFlujo(Exception):
    def __init__(self, codigo: int, mensaje: str, motivo: str = "error"):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.motivo = motivo


class ErrorA2A(ErrorFlujo):
    """Fallo al delegar en otro agente por A2A."""
