"""Fabrica de modelos con timeout, reintento acotado y respaldo.

Reglas de resiliencia:
- Toda llamada al modelo tiene timeout explicito (TIMEOUT_LLM_S).
- max_retries=1: nunca se reintenta indefinidamente.
- Si el modelo principal falla, se usa UN modelo de respaldo
  (MODELO_RESPALDO) y se registra el evento `modelo_respaldo_usado`.
- Si el respaldo tambien falla, el error sube y el flujo responde
  con un mensaje claro, sin inventar resultados.
"""

from typing import Any, Callable

from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI

from config import obtener_config
from registro.bitacora import evento


class FalloSimuladoDelModelo(RuntimeError):
    """Error provocado a proposito para demostrar el respaldo."""


class ModeloQueFalla(BaseChatModel):
    """Modelo principal de prueba que siempre falla.

    Se activa con la cabecera X-Simular-Fallo: modelo.
    """

    @property
    def _llm_type(self) -> str:
        return "modelo-que-falla"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ModeloQueFalla":
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any) -> "ModeloQueFalla":
        return self

    def _generate(self, messages: list[BaseMessage], stop=None,
                  run_manager=None, **kwargs: Any) -> ChatResult:
        raise FalloSimuladoDelModelo("Fallo simulado del modelo principal")

    def invoke(self, *args: Any, **kwargs: Any):
        raise FalloSimuladoDelModelo("Fallo simulado del modelo principal")

    async def ainvoke(self, *args: Any, **kwargs: Any):
        raise FalloSimuladoDelModelo("Fallo simulado del modelo principal")


def crear_modelo_gemini(nombre: str, temperatura: float | None = None) -> BaseChatModel:
    config = obtener_config()
    parametros: dict[str, Any] = {
        "model": nombre,
        "timeout": config.timeout_llm_s,
        "max_retries": 1,
    }
    if temperatura is not None:
        parametros["temperature"] = temperatura
    return ChatGoogleGenerativeAI(**parametros)


def crear_modelos(temperatura: float | None = None,
                  simular_fallo: bool = False) -> tuple[BaseChatModel, BaseChatModel]:
    """Devuelve (principal, respaldo)."""

    config = obtener_config()
    respaldo = crear_modelo_gemini(config.modelo_respaldo, temperatura)
    if simular_fallo:
        return ModeloQueFalla(), respaldo
    return crear_modelo_gemini(config.modelo, temperatura), respaldo


def resumir_error(error: Exception, largo: int = 160) -> str:
    """Short provider error for the log (status and message, no secrets)."""
    return " ".join(str(error).split())[:largo]


def _registrar_respaldo(error: Exception) -> None:
    evento(
        "modelo_respaldo_usado",
        motivo=type(error).__name__,
        detalle=resumir_error(error),
        modelo_respaldo=obtener_config().modelo_respaldo,
    )


class RespaldoDeModelo(AgentMiddleware):
    """Middleware de create_agent: un unico respaldo por llamada."""

    def __init__(self, respaldo: BaseChatModel):
        super().__init__()
        self.respaldo = respaldo

    def wrap_model_call(self, request, handler):
        try:
            return handler(request)
        except Exception as error:
            _registrar_respaldo(error)
            return handler(request.override(model=self.respaldo))

    async def awrap_model_call(self, request, handler):
        try:
            return await handler(request)
        except Exception as error:
            _registrar_respaldo(error)
            return await handler(request.override(model=self.respaldo))


async def invocar_con_respaldo(
    construir: Callable[[BaseChatModel], Any],
    entrada: Any,
    temperatura: float | None = None,
    simular_fallo: bool = False,
) -> Any:
    """Invoca un runnable construido sobre el modelo principal.

    Si falla, reconstruye el mismo runnable sobre el respaldo.
    """

    principal, respaldo = crear_modelos(temperatura, simular_fallo)
    try:
        return await construir(principal).ainvoke(entrada)
    except Exception as error:
        _registrar_respaldo(error)
        return await construir(respaldo).ainvoke(entrada)
