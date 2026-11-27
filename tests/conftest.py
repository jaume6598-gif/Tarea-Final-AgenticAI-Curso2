"""Configuracion de pruebas: sin red ni LLM real."""

import itertools
import os

# Variables de prueba ANTES de importar la aplicacion.
os.environ.update({
    "APP_API_TOKEN": "token-lector-prueba",
    "APP_ADMIN_TOKEN": "token-admin-prueba",
    "A2A_TOKEN": "token-a2a-prueba",
    "PERMITIR_SIMULACION_FALLOS": "true",
    "GOOGLE_API_KEY": "clave-falsa-de-prueba",
    "MAX_LLAMADAS_HERRAMIENTA": "4",
    "MAX_PASOS_REACT": "25",
    "URL_GERARDO": "http://127.0.0.1:9",
    "TIMEOUT_A2A_S": "3",
})

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langchain_core.language_models.fake_chat_models import (  # noqa: E402
    GenericFakeChatModel,
)
from langchain_core.messages import AIMessage  # noqa: E402

LECTOR = {"X-API-Key": "token-lector-prueba"}
ADMIN = {"X-API-Key": "token-admin-prueba"}


class ModeloFalso(GenericFakeChatModel):
    """Modelo de chat falso que acepta herramientas."""

    def bind_tools(self, tools, **kwargs):
        return self


def modelo_con(*mensajes):
    return ModeloFalso(messages=iter(mensajes))


def llamada(nombre, **args):
    return AIMessage(content="", tool_calls=[{
        "name": nombre, "args": args, "id": f"llamada-{nombre}",
    }])


def modelo_que_siempre_llama(nombre, **args):
    return ModeloFalso(messages=(
        AIMessage(content="", tool_calls=[{
            "name": nombre, "args": args, "id": f"llamada-{i}",
        }])
        for i in itertools.count()
    ))


@pytest.fixture
def cliente():
    from main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def estado_limpio(monkeypatch):
    from datos.inventario import inventario
    from agentes.jaime.agente import obtener_agente_jaime
    from seguridad.aprobaciones import aprobaciones

    async def sin_mcp():
        return []
    monkeypatch.setattr("agentes.jaime.react.obtener_herramientas_mcp", sin_mcp)
    inventario.reiniciar()
    aprobaciones.reiniciar()
    obtener_agente_jaime.cache_clear()
    yield
    inventario.reiniciar()
    aprobaciones.reiniciar()
    obtener_agente_jaime.cache_clear()


@pytest.fixture
def modelos_falsos(monkeypatch):
    """Reemplaza (principal, respaldo) del agente Jaime."""

    def aplicar(principal, respaldo=None):
        respaldo = respaldo or modelo_con(AIMessage(content="respaldo"))
        monkeypatch.setattr(
            "agentes.jaime.agente.crear_modelos",
            lambda **_: (principal, respaldo),
        )
    return aplicar


@pytest.fixture
def router_fijo(monkeypatch):
    from agentes.jaime.router import Decision

    def aplicar(flujo):
        async def falso(consulta, simular_fallo=False):
            return Decision(flujo=flujo, motivo=f"prueba {flujo}")
        monkeypatch.setattr("agentes.jaime.grafo.seleccionar_flujo", falso)
    return aplicar
