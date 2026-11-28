"""Cliente MCP de Jaime (langchain-mcp-adapters).

- Solo se aceptan herramientas de la allowlist TOOLS_PERMITIDAS.
- Timeout explicito por llamada.
- Si el servidor MCP no responde, Jaime sigue funcionando con sus
  herramientas locales y se registra `mcp_no_disponible`.
"""

import logging
import time

from langchain_mcp_adapters.client import MultiServerMCPClient

from config import obtener_config
from registro.bitacora import evento

logger = logging.getLogger("sistema_agentes")

TOOLS_PERMITIDAS = {"consultar_proveedor", "registro_temperaturas"}
TIMEOUT_MCP_S = 10
REINTENTO_TRAS_FALLO_S = 60

_cache: dict = {"herramientas": None, "fallo_en": 0.0}


def _token() -> str:
    config = obtener_config()
    return config.mcp_token or config.a2a_token


def _causa(error: BaseException) -> str:
    """Unwraps anyio ExceptionGroups to show the real cause."""
    while isinstance(error, BaseExceptionGroup) and error.exceptions:
        error = error.exceptions[0]
    return f"{type(error).__name__}: {' '.join(str(error).split())[:160]}"


async def obtener_herramientas_mcp() -> list:
    """Carga (una vez) las herramientas MCP permitidas."""

    if _cache["herramientas"] is not None:
        return _cache["herramientas"]
    if time.monotonic() - _cache["fallo_en"] < REINTENTO_TRAS_FALLO_S:
        return []

    config = obtener_config()
    cliente = MultiServerMCPClient({
        "proveedores": {
            "transport": "streamable_http",
            "url": config.mcp_url,
            "headers": {"Authorization": f"Bearer {_token()}"},
            "timeout": TIMEOUT_MCP_S,
        }
    })
    try:
        todas = await cliente.get_tools()
    except Exception as error:
        _cache["fallo_en"] = time.monotonic()
        causa = _causa(error)
        logger.warning("MCP no disponible: %s", causa)
        evento("mcp_no_disponible", motivo=type(error).__name__, detalle=causa,
               url=config.mcp_url or "(vacia)",
               ruta_respaldo="solo_herramientas_locales")
        return []

    permitidas = [h for h in todas if h.name in TOOLS_PERMITIDAS]
    ignoradas = sorted(h.name for h in todas if h.name not in TOOLS_PERMITIDAS)
    if ignoradas:
        logger.info("Herramientas MCP ignoradas por allowlist: %s", ignoradas)
    _cache["herramientas"] = permitidas
    return permitidas


def nombres_mcp() -> set[str]:
    return {h.name for h in (_cache["herramientas"] or [])}


def reiniciar_cache() -> None:
    _cache.update(herramientas=None, fallo_en=0.0)
