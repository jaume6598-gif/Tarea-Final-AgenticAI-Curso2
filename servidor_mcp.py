"""Servidor MCP interno: proveedores y registro de temperaturas.

Estos datos NO estan en las herramientas locales de Jaime: el agente
solo puede obtenerlos llamando a este servidor por MCP.

- Transporte: streamable HTTP en /mcp
- Autenticacion: Authorization: Bearer MCP_TOKEN (o A2A_TOKEN si no se define)

Ejecucion local:
    python -m uvicorn servidor_mcp:app --port 8002
"""

import json
import secrets
import unicodedata
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from config import obtener_config

DATOS = json.loads(
    (Path(__file__).parent / "datos" / "proveedores.json").read_text(encoding="utf-8")
)
LIMITE_TEMPERATURA_C = 5.0

mcp = FastMCP(
    name="proveedores-minimarket",
    instructions="Datos de proveedores y temperaturas de camaras del minimarket.",
    stateless_http=True,
    json_response=True,
)


def _normalizar(texto: str) -> str:
    """Lowercase without accents: 'Lácteos Sur' matches 'Lacteos Sur'."""
    descompuesto = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _buscar(nombre: str, opciones: dict) -> str | None:
    termino = _normalizar(nombre)
    for clave in opciones:
        candidato = _normalizar(clave)
        if termino and (termino in candidato or candidato in termino):
            return clave
    return None


@mcp.tool()
def consultar_proveedor(nombre: str) -> str:
    """Datos comerciales de un proveedor: contacto, dias de entrega
    (lead time), pedido minimo y dias de despacho."""

    clave = _buscar(nombre, DATOS["proveedores"])
    if clave is None:
        return (f"No hay un proveedor llamado '{nombre}'. Proveedores: "
                + ", ".join(DATOS["proveedores"]))
    datos = DATOS["proveedores"][clave]
    return (f"{clave}: contacto {datos['contacto']}, entrega en "
            f"{datos['dias_entrega']} dias, pedido minimo "
            f"{datos['pedido_minimo_unidades']} unidades, despacha "
            f"{', '.join(datos['dias_despacho'])}.")


@mcp.tool()
def registro_temperaturas(camara: str) -> str:
    """Registro reciente de temperatura de una camara de frio e indica
    si hubo lecturas sobre el limite de 5 °C."""

    clave = _buscar(camara, DATOS["temperaturas"])
    if clave is None:
        return (f"No hay registro para '{camara}'. Camaras: "
                + ", ".join(DATOS["temperaturas"]))
    lecturas = DATOS["temperaturas"][clave]
    fuera = [l for l in lecturas if l["c"] > LIMITE_TEMPERATURA_C]
    detalle = "; ".join(f"{l['fecha']}: {l['c']} °C" for l in lecturas)
    alerta = (f"ALERTA: {len(fuera)} lecturas sobre {LIMITE_TEMPERATURA_C} °C."
              if fuera else "Todas las lecturas dentro del limite.")
    return f"{clave} -> {detalle}. {alerta}"


def token_mcp() -> str:
    config = obtener_config()
    return config.mcp_token or config.a2a_token


class AutenticacionMCP(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/mcp"):
            esperado = token_mcp()
            recibido = request.headers.get("authorization", "")
            if not esperado or not secrets.compare_digest(
                recibido, f"Bearer {esperado}"
            ):
                return JSONResponse({"error": "Acceso MCP no autorizado"},
                                    status_code=401)
        return await call_next(request)


async def salud(_request):
    return JSONResponse({"ok": True, "servidor": "mcp-proveedores"})


app = mcp.streamable_http_app()
app.router.routes.append(Route("/salud", salud))
app.add_middleware(AutenticacionMCP)
