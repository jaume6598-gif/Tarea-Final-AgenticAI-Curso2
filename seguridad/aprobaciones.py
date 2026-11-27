"""Aprobacion humana (human-in-the-loop) de mermas.

El agente nunca descuenta stock por si solo: `registrar_merma` crea una
solicitud PENDIENTE. Solo un administrador, via POST /aprobaciones/{id},
decide aprobar (se descuenta el stock) o rechazar (no cambia nada).
La decision humana cambia el resultado de la accion propuesta por el agente.
"""

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock

from datos.inventario import inventario
from registro.bitacora import ejecucion_actual, evento

PENDIENTE = "pendiente"
APROBADA = "aprobada"
RECHAZADA = "rechazada"


@dataclass
class SolicitudMerma:
    id: str
    lote: str
    cantidad: int
    motivo: str
    estado: str = PENDIENTE
    creada: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    id_ejecucion: str | None = None
    decidida_por: str | None = None
    comentario: str | None = None
    stock_antes: int | None = None
    stock_despues: int | None = None

    def como_dict(self) -> dict:
        return asdict(self)


class ErrorAprobacion(ValueError):
    pass


class RegistroAprobaciones:
    def __init__(self):
        self._solicitudes: dict[str, SolicitudMerma] = {}
        self._candado = Lock()

    def crear(self, lote: str, cantidad: int, motivo: str) -> SolicitudMerma:
        lote = lote.strip().upper()
        if inventario.obtener(lote) is None:
            raise ErrorAprobacion(f"El lote {lote} no existe.")
        if cantidad <= 0:
            raise ErrorAprobacion("La cantidad debe ser mayor que cero.")
        ejecucion = ejecucion_actual()
        solicitud = SolicitudMerma(
            id=f"MER-{uuid.uuid4().hex[:8].upper()}",
            lote=lote,
            cantidad=cantidad,
            motivo=motivo,
            id_ejecucion=ejecucion.id_ejecucion if ejecucion else None,
        )
        with self._candado:
            self._solicitudes[solicitud.id] = solicitud
        evento("aprobacion_pendiente", id_solicitud=solicitud.id, lote=lote,
               cantidad=cantidad, motivo=motivo)
        return solicitud

    def listar(self, estado: str | None = None) -> list[SolicitudMerma]:
        with self._candado:
            return [s for s in self._solicitudes.values()
                    if estado is None or s.estado == estado]

    def obtener(self, id_solicitud: str) -> SolicitudMerma | None:
        return self._solicitudes.get(id_solicitud)

    def decidir(self, id_solicitud: str, aprobar: bool,
                responsable: str, comentario: str | None = None) -> SolicitudMerma:
        with self._candado:
            solicitud = self._solicitudes.get(id_solicitud)
            if solicitud is None:
                raise ErrorAprobacion("Solicitud no encontrada.")
            if solicitud.estado != PENDIENTE:
                raise ErrorAprobacion(f"La solicitud ya fue {solicitud.estado}.")
            lote = inventario.obtener(solicitud.lote)
            solicitud.stock_antes = lote.stock if lote else None
            if aprobar:
                solicitud.stock_despues = inventario.descontar(
                    solicitud.lote, solicitud.cantidad
                )
                solicitud.estado = APROBADA
            else:
                solicitud.stock_despues = solicitud.stock_antes
                solicitud.estado = RECHAZADA
            solicitud.decidida_por = responsable
            solicitud.comentario = comentario
        evento("aprobacion_decidida", id_solicitud=id_solicitud,
               estado=solicitud.estado, stock_antes=solicitud.stock_antes,
               stock_despues=solicitud.stock_despues)
        return solicitud

    def reiniciar(self) -> None:
        with self._candado:
            self._solicitudes.clear()


aprobaciones = RegistroAprobaciones()
