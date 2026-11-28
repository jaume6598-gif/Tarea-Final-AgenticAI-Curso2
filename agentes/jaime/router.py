"""Rol router de Jaime: clasifica la solicitud con salida estructurada.

El mismo agente Jaime (misma identidad y especialidad) primero decide
el flujo y luego lo ejecuta como worker en el grafo.
"""

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from agentes.jaime.prompt_router import SYSTEM_ROUTER
from agentes.modelos import invocar_con_respaldo

FLUJOS_VALIDOS = ("OPERACIONES", "TECNOLOGIA", "TRAZABILIDAD", "REPOSICION", "RECHAZO")


class Decision(BaseModel):
    flujo: Literal["OPERACIONES", "TECNOLOGIA", "TRAZABILIDAD", "REPOSICION",
                   "RECHAZO"] = Field(
        description="Flujo que debe ejecutar Jaime."
    )
    motivo: str = Field(description="Una frase: por qué ese flujo.")


async def seleccionar_flujo(consulta: str, simular_fallo: bool = False) -> Decision:
    """Clasifica una consulta; valida la decision independientemente del LLM."""

    if not consulta.strip():
        raise ValueError("La consulta esta vacia.")

    decision = await invocar_con_respaldo(
        lambda modelo: modelo.with_structured_output(Decision),
        [
            SystemMessage(content=SYSTEM_ROUTER),
            HumanMessage(content=f"<consulta>{consulta}</consulta>"),
        ],
        temperatura=0,
        simular_fallo=simular_fallo,
    )

    if not isinstance(decision, Decision) or decision.flujo not in FLUJOS_VALIDOS:
        raise ValueError("Respuesta invalida del Router.")
    return decision
