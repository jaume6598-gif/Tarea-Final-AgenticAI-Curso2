from langchain.agents import create_agent

from agentes.gerardo.herramientas import HERRAMIENTAS
from agentes.gerardo.prompts import SYSTEM_VIAJES
from agentes.modelos import RespaldoDeModelo, crear_modelos


def crear_agente_gerardo():
    principal, respaldo = crear_modelos()

    return create_agent(
        model=principal,
        tools=HERRAMIENTAS,
        system_prompt=SYSTEM_VIAJES,
        middleware=[RespaldoDeModelo(respaldo)],
        name="agente_gerardo",
    )
