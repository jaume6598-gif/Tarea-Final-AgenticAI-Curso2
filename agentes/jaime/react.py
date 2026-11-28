"""Ejecucion del ciclo ReAct de Jaime con traza observable."""

import logging

from langgraph.errors import GraphRecursionError

from agentes.errores import ErrorFlujo
from agentes.jaime.agente import obtener_agente_jaime
from agentes.jaime.mcp_cliente import nombres_mcp, obtener_herramientas_mcp
from config import obtener_config
from memoria import persistencia as memoria
from registro.bitacora import evento

logger = logging.getLogger("sistema_agentes")

PREFIJO_LIMITE = "Tool call limit exceeded"


def extraer_texto(contenido) -> str:
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        return "\n".join(
            bloque.get("text", "")
            for bloque in contenido
            if isinstance(bloque, dict) and bloque.get("type") == "text"
        )
    return ""


def analizar_resultado(mensajes) -> tuple[str, list[dict], str]:
    """Extrae (respuesta, traza, motivo_parada) de los mensajes ReAct."""

    traza: list[dict] = []
    limite_alcanzado = False

    for mensaje in mensajes:
        for llamada in getattr(mensaje, "tool_calls", None) or []:
            traza.append({
                "evento": "decision_herramienta",
                "herramienta": llamada["name"],
                "argumentos": llamada.get("args", {}),
            })
        if mensaje.type == "tool":
            contenido = extraer_texto(mensaje.content)
            if contenido.startswith(PREFIJO_LIMITE):
                limite_alcanzado = True
            traza.append({
                "evento": "resultado_herramienta",
                "herramienta": mensaje.name,
                "resultado": contenido[:300],
            })

    ultimo = mensajes[-1]

    if limite_alcanzado:
        motivo = "limite_herramientas"
        texto = (
            "Alcance el limite de consultas a herramientas "
            f"({obtener_config().max_llamadas_herramienta}) sin una respuesta "
            "final. No entrego conclusiones sin evidencia; reformula la "
            "consulta con un alcance mas acotado."
        )
    else:
        if ultimo.type != "ai" or getattr(ultimo, "tool_calls", None):
            raise ErrorFlujo(502, "El agente no finalizo correctamente")
        texto = extraer_texto(ultimo.content)
        if not texto.strip():
            raise ErrorFlujo(502, "El agente devolvio una respuesta vacia")
        motivo = "respuesta_final"

    traza.append({"evento": "parada", "motivo": motivo})
    return texto, traza, motivo


async def ejecutar_react(instruccion: str, simular_fallo: bool = False,
                         agente=None, hilo: str | None = None) -> tuple[str, list[dict]]:
    """Ejecuta Jaime con tope de pasos y de herramientas.

    Con `hilo`, el agente usa el checkpointer: retoma la conversacion
    guardada de ese hilo (memoria persistente si hay Postgres).
    """

    config = obtener_config()
    guardado = memoria.checkpointer() if hilo else None
    if agente is None:
        herramientas_mcp = await obtener_herramientas_mcp()
        agente = obtener_agente_jaime(simular_fallo, herramientas_mcp, guardado)

    config_ejecucion: dict = {"recursion_limit": config.max_pasos_react}
    previos = 0
    if guardado is not None:
        config_ejecucion["configurable"] = {"thread_id": hilo}
        estado_previo = await agente.aget_state(config_ejecucion)
        previos = len((estado_previo.values or {}).get("messages", []))
        evento("memoria_recuperada", hilo=hilo, mensajes_previos=previos,
               almacenamiento=memoria.tipo())

    try:
        resultado = await agente.ainvoke(
            {"messages": [{"role": "user", "content": instruccion}]},
            config=config_ejecucion,
        )
    except GraphRecursionError:
        evento("parada", motivo="limite_pasos",
               limite=config.max_pasos_react)
        raise ErrorFlujo(
            504,
            "El agente alcanzo el limite de pasos sin una respuesta final.",
            motivo="limite_pasos",
        )
    except ErrorFlujo:
        raise
    except Exception as error:
        logger.exception("Fallo al ejecutar Jaime")
        raise ErrorFlujo(
            502,
            "Jaime no pudo completar la tarea (modelo principal y de "
            f"respaldo no disponibles: {type(error).__name__}).",
            motivo="modelo_no_disponible",
        )

    # Only this run's messages: earlier turns of the thread are context.
    texto, traza, motivo = analizar_resultado(resultado["messages"][previos:])
    remotas = nombres_mcp()
    for paso in traza:
        if paso.get("herramienta") in remotas:
            paso["origen"] = "mcp"
            if paso["evento"] == "resultado_herramienta":
                evento("llamada_mcp", herramienta=paso["herramienta"],
                       resultado=paso.get("resultado", "")[:200])
        if paso["evento"] in {"decision_herramienta", "parada"}:
            evento(paso["evento"], **{k: v for k, v in paso.items()
                                      if k != "evento"})
    return texto, traza
