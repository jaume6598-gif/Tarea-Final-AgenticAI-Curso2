"""Agente Jaime (worker ReAct).

Ciclo ReAct: el modelo decide llamar una herramienta, recibe el
resultado y decide si continua o responde.

Condiciones de parada explicitas:
1. respuesta_final: el modelo responde sin pedir herramientas.
2. limite_herramientas: se alcanzan MAX_LLAMADAS_HERRAMIENTA llamadas
   (ToolCallLimitMiddleware con exit_behavior="end").
3. limite_pasos: se alcanzan MAX_PASOS_REACT pasos del grafo
   (recursion_limit -> GraphRecursionError).
"""

from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware

from agentes.jaime.herramientas import HERRAMIENTAS
from agentes.jaime.prompts import SYSTEM_JAIME
from agentes.modelos import RespaldoDeModelo, crear_modelos
from config import obtener_config


def crear_agente_jaime(simular_fallo: bool = False, herramientas=None):
    config = obtener_config()
    principal, respaldo = crear_modelos(simular_fallo=simular_fallo)

    return create_agent(
        model=principal,
        tools=herramientas or HERRAMIENTAS,
        system_prompt=SYSTEM_JAIME,
        middleware=[
            RespaldoDeModelo(respaldo),
            ToolCallLimitMiddleware(
                run_limit=config.max_llamadas_herramienta,
                exit_behavior="end",
            ),
        ],
        name="agente_jaime",
    )


_agentes: dict = {}


def obtener_agente_jaime(simular_fallo: bool = False, herramientas_extra=()):
    """El agente se compila una sola vez por modo y conjunto de herramientas."""

    clave = (simular_fallo, tuple(sorted(h.name for h in herramientas_extra)))
    if clave not in _agentes:
        _agentes[clave] = crear_agente_jaime(
            simular_fallo=simular_fallo,
            herramientas=[*HERRAMIENTAS, *herramientas_extra],
        )
    return _agentes[clave]


obtener_agente_jaime.cache_clear = _agentes.clear
