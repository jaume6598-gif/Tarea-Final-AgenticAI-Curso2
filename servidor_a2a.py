
import uvicorn

from starlette.applications import Starlette
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentInterface, AgentSkill
from a2a.helpers import get_message_text, new_text_message

from agentes.gerardo.agente import crear_agente_gerardo


# Conecta las solicitudes A2A con nuestro agente Gerardo.
class EjecutorGerardo(AgentExecutor):

    def __init__(self):
        self.agente = crear_agente_gerardo()

    async def execute(self, context: RequestContext,
                      event_queue: EventQueue):

        consulta = get_message_text(context.message)
        print("A2A - Gerardo recibió:", consulta)

        if not consulta.strip():
            await event_queue.enqueue_event(
                new_text_message("Falta indicar la consulta.")
            )
            return

        resultado = await self.agente.ainvoke({
            "messages": [{"role": "user", "content": consulta}]
        })

        contenido = resultado["messages"][-1].content
        if isinstance(contenido, str):
            respuesta = contenido
        else:
            respuesta = "\n".join(
                bloque.get("text", "")
                for bloque in contenido
                if isinstance(bloque, dict)
                and bloque.get("type") == "text"
            )

        await event_queue.enqueue_event(
            new_text_message(respuesta)
        )
        print("A2A - Gerardo respondió.")

    async def cancel(self, context: RequestContext,
                     event_queue: EventQueue):
        raise NotImplementedError("Cancelación no disponible")


# Tarjeta pública A2A de Gerardo.
tarjeta = AgentCard(
    name="Agente Gerardo",
    description="Especialista en arquitectura de software e IA.",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supported_interfaces=[
        AgentInterface(
            protocol_binding="JSONRPC",
            url="http://127.0.0.1:8001/",
            protocol_version="1.0",
        )
    ],
    skills=[
        AgentSkill(
            id="arquitectura",
            name="Diseño tecnológico",
            description="Propone soluciones tecnológicas sencillas.",
            tags=["arquitectura", "IA"],
        )
    ],
)

manejador = DefaultRequestHandler(
    agent_executor=EjecutorGerardo(),
    task_store=InMemoryTaskStore(),
    agent_card=tarjeta,
)

rutas = [
    *create_agent_card_routes(tarjeta),
    *create_jsonrpc_routes(manejador, "/"),
]

app = Starlette(routes=rutas)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
