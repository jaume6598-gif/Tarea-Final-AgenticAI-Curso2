"""Bitacora de ejecuciones.

Cada solicitud abre una Ejecucion. Los nodos, herramientas y
middleware agregan eventos con `evento(...)` sin recibir la
ejecucion como parametro: se usa una ContextVar.

El docente consulta el resultado con GET /registros/{id}.
"""

import json
import logging
import time
import uuid
from collections import OrderedDict
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("sistema_agentes")

ESTADOS_FINALES = {"completado", "parcial", "bloqueado", "error"}
MAX_EJECUCIONES = 200


@dataclass
class Ejecucion:
    id_ejecucion: str
    inicio: str
    pregunta: str
    flujo: str | None = None
    estado: str = "en_curso"
    duracion_ms: int | None = None
    eventos: list[dict[str, Any]] = field(default_factory=list)
    _t0: float = field(default_factory=time.perf_counter, repr=False)

    def como_dict(self) -> dict[str, Any]:
        return {
            "id_ejecucion": self.id_ejecucion,
            "inicio": self.inicio,
            "pregunta": self.pregunta,
            "flujo": self.flujo,
            "estado": self.estado,
            "duracion_ms": self.duracion_ms,
            "eventos": list(self.eventos),
        }


_actual: ContextVar[Ejecucion | None] = ContextVar(
    "ejecucion_actual", default=None
)


def _log(id_ejecucion: str, nombre: str, datos: dict[str, Any]) -> None:
    logger.info(json.dumps(
        {"id_ejecucion": id_ejecucion, "evento": nombre, **datos},
        ensure_ascii=False,
        default=str,
    ))


def evento(nombre: str, **datos: Any) -> None:
    """Agrega un evento a la ejecucion en curso (si existe)."""

    ejecucion = _actual.get()
    if ejecucion is None:
        _log("-", nombre, datos)
        return
    ejecucion.eventos.append({"evento": nombre, **datos})
    _log(ejecucion.id_ejecucion, nombre, datos)


def ejecucion_actual() -> Ejecucion | None:
    return _actual.get()


class Bitacora:
    """Almacen en memoria de las ultimas ejecuciones."""

    def __init__(self, maximo: int = MAX_EJECUCIONES):
        self._maximo = maximo
        self._ejecuciones: OrderedDict[str, Ejecucion] = OrderedDict()
        self._persistir = None

    def configurar_persistencia(self, funcion) -> None:
        """Registra una funcion que guarda la ejecucion final."""
        self._persistir = funcion

    def iniciar(self, pregunta: str) -> Ejecucion:
        ejecucion = Ejecucion(
            id_ejecucion=str(uuid.uuid4()),
            inicio=datetime.now(timezone.utc).isoformat(),
            pregunta=pregunta,
        )
        self._ejecuciones[ejecucion.id_ejecucion] = ejecucion
        while len(self._ejecuciones) > self._maximo:
            self._ejecuciones.popitem(last=False)
        _actual.set(ejecucion)
        _log(ejecucion.id_ejecucion, "inicio", {})
        return ejecucion

    def finalizar(self, ejecucion: Ejecucion, estado: str, **datos: Any) -> None:
        if estado not in ESTADOS_FINALES:
            raise ValueError(f"Estado final invalido: {estado}")
        ejecucion.estado = estado
        ejecucion.duracion_ms = int(
            (time.perf_counter() - ejecucion._t0) * 1000
        )
        ejecucion.eventos.append({"evento": "fin", "estado": estado, **datos})
        _log(ejecucion.id_ejecucion, "fin", {
            "flujo": ejecucion.flujo,
            "estado": estado,
            "duracion_ms": ejecucion.duracion_ms,
            **datos,
        })
        if self._persistir is not None:
            try:
                self._persistir(ejecucion)
            except Exception as error:  # la persistencia nunca rompe la API
                logger.warning("No se pudo persistir la ejecucion: %s",
                               type(error).__name__)

    def obtener(self, id_ejecucion: str) -> Ejecucion | None:
        return self._ejecuciones.get(id_ejecucion)

    def listar(self, limite: int = 20) -> list[Ejecucion]:
        return list(reversed(self._ejecuciones.values()))[:limite]


bitacora = Bitacora()
