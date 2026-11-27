"""Servidor A2A del agente especialista Gerardo.

- GET  /.well-known/agent-card.json  -> publico
- GET  /salud                         -> publico
- POST /  (JSON-RPC SendMessage)      -> requiere Authorization: Bearer A2A_TOKEN
"""

import logging
import secrets

import uvicorn
from a2a.helpers import get_message_text, new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from agentes.gerardo.agente import crear_agente_gerardo
from agentes.jaime.react import extraer_texto
from config import obtener_config

logger = logging.getLogger("gerardo_a2a")
logging.basicConfig(level=logging.INFO)


class EjecutorGerardo(AgentExecutor):
    """Conecta las solicitudes A2A con el agente Gerardo."""

    def __init__(self):
        self.agente = crear_agente_gerardo()

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        consulta = get_message_text(context.message)
        logger.info("A2A - Gerardo recibio un encargo (%d caracteres)",
                    len(consulta))

        if not consulta.strip():
            await event_queue.enqueue_event(
                new_text_message("Falta indicar la consulta.")
            )
            return

        try:
            resultado = await self.agente.ainvoke(
                {"messages": [{"role": "user", "content": consulta}]},
                config={"recursion_limit": obtener_config().max_pasos_react},
            )
            respuesta = extraer_texto(resultado["messages"][-1].content)
            if not respuesta.strip():
                raise ValueError("respuesta vacia")
        except Exception as error:
            logger.warning("Gerardo no pudo responder: %s", type(error).__name__)
            # El cliente distingue este prefijo y no lo trata como propuesta.
            respuesta = ("ERROR_ESPECIALISTA: Gerardo no pudo generar la "
                         "propuesta en este momento.")

        await event_queue.enqueue_event(new_text_message(respuesta))
        logger.info("A2A - Gerardo respondio.")

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise NotImplementedError("Cancelacion no disponible")


def crear_tarjeta(url: str) -> AgentCard:
    return AgentCard(
        name="Agente Gerardo",
        description=(
            "Especialista en arquitectura de software e IA: propone "
            "soluciones tecnologicas sencillas a partir de requisitos. "
            "No ejecuta cambios ni accede a datos de inventario."
        ),
        version="1.1.0",
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                url=url.rstrip("/") + "/",
                protocol_version="1.0",
            )
        ],
        skills=[
            AgentSkill(
                id="arquitectura",
                name="Diseno tecnologico",
                description="Propone soluciones tecnologicas sencillas.",
                tags=["arquitectura", "IA"],
                examples=["Propone una arquitectura simple para "
                          "gestionar inventario FEFO."],
            )
        ],
    )


class AutenticacionA2A(BaseHTTPMiddleware):
    """Exige Bearer token en POST; tarjeta y salud quedan publicas."""

    async def dispatch(self, request, call_next):
        if request.method == "POST":
            esperado = obtener_config().a2a_token
            recibido = request.headers.get("authorization", "")
            if not esperado or not secrets.compare_digest(
                recibido, f"Bearer {esperado}"
            ):
                return JSONResponse(
                    {"error": "Acceso A2A no autorizado"}, status_code=401
                )
        return await call_next(request)


async def salud(_request):
    return JSONResponse({"ok": True, "agente": "Gerardo"})


def crear_app() -> Starlette:
    tarjeta = crear_tarjeta(obtener_config().url_gerardo)
    manejador = DefaultRequestHandler(
        agent_executor=EjecutorGerardo(),
        task_store=InMemoryTaskStore(),
        agent_card=tarjeta,
    )
    rutas = [
        *create_agent_card_routes(tarjeta),
        Route("/salud", salud),
        *create_jsonrpc_routes(manejador, "/"),
    ]
    aplicacion = Starlette(routes=rutas)
    aplicacion.add_middleware(AutenticacionA2A)
    return aplicacion


app = crear_app()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
