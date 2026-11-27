"""Politica de acciones con efecto real.

El alcance de la solicitud ('lector' o 'admin') lo fija la API segun
el token recibido. Las herramientas sensibles consultan esta politica
ANTES de ejecutar: si el alcance no alcanza, la accion se bloquea sin
ejecutarse, aunque el LLM haya decidido llamarla.
"""

from contextvars import ContextVar

from registro.bitacora import evento

ALCANCE_LECTOR = "lector"
ALCANCE_ADMIN = "admin"

ACCIONES_PROTEGIDAS = {
    "eliminar_lote": ALCANCE_ADMIN,
}

_alcance: ContextVar[str] = ContextVar("alcance", default=ALCANCE_LECTOR)


def fijar_alcance(alcance: str) -> None:
    _alcance.set(alcance)


def alcance_actual() -> str:
    return _alcance.get()


def autorizar(accion: str, **argumentos) -> bool:
    """Devuelve True si la accion puede ejecutarse; registra el bloqueo."""

    requerido = ACCIONES_PROTEGIDAS.get(accion)
    if requerido is None or alcance_actual() == requerido:
        return True
    evento(
        "accion_bloqueada",
        accion=accion,
        argumentos=argumentos,
        alcance=alcance_actual(),
        requerido=requerido,
    )
    return False


MENSAJE_BLOQUEO = (
    "BLOQUEADO: accion no autorizada para este acceso. "
    "No se ejecuto ningun cambio. Requiere alcance de administrador."
)
