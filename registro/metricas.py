"""Observabilidad: tokens por ejecucion y metricas agregadas.

- ContadorTokens: callback de LangChain que suma usage_metadata de cada
  llamada al modelo (router, ReAct, respaldo) en la ejecucion en curso.
- resumen(): metricas para GET /metricas (conteos, latencias, tokens).
"""

from collections import Counter
from statistics import quantiles
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from registro.bitacora import Bitacora, ejecucion_actual


class ContadorTokens(BaseCallbackHandler):
    def on_llm_end(self, response, **kwargs: Any) -> None:
        ejecucion = ejecucion_actual()
        if ejecucion is None:
            return
        uso = ejecucion.uso
        uso["llamadas_llm"] += 1
        for generaciones in response.generations:
            for generacion in generaciones:
                mensaje = getattr(generacion, "message", None)
                metadata = getattr(mensaje, "usage_metadata", None) or {}
                uso["tokens_entrada"] += metadata.get("input_tokens", 0)
                uso["tokens_salida"] += metadata.get("output_tokens", 0)
                modelo = (getattr(mensaje, "response_metadata", None) or {}).get(
                    "model_name"
                )
                if modelo:
                    uso["modelos"][modelo] = uso["modelos"].get(modelo, 0) + 1


def _percentil(valores: list[int], p: int) -> int | None:
    if not valores:
        return None
    if len(valores) == 1:
        return valores[0]
    return int(quantiles(valores, n=100, method="inclusive")[p - 1])


def resumen(bitacora: Bitacora) -> dict:
    terminadas = [e for e in bitacora.listar(10_000) if e.duracion_ms is not None]
    duraciones = [e.duracion_ms for e in terminadas]
    con_llm = [e for e in terminadas if e.uso["llamadas_llm"]]
    eventos = Counter(
        evento["evento"] for e in terminadas for evento in e.eventos
    )
    return {
        "ejecuciones": len(terminadas),
        "por_flujo": dict(Counter(e.flujo or "sin_flujo" for e in terminadas)),
        "por_estado": dict(Counter(e.estado for e in terminadas)),
        "latencia_ms": {
            "p50": _percentil(duraciones, 50),
            "p95": _percentil(duraciones, 95),
            "max": max(duraciones) if duraciones else None,
        },
        "tokens": {
            "entrada_total": sum(e.uso["tokens_entrada"] for e in terminadas),
            "salida_total": sum(e.uso["tokens_salida"] for e in terminadas),
            "promedio_por_ejecucion_con_llm": (
                round(sum(e.uso["tokens_entrada"] + e.uso["tokens_salida"]
                          for e in con_llm) / len(con_llm))
                if con_llm else None
            ),
            "llamadas_llm_total": sum(e.uso["llamadas_llm"] for e in terminadas),
        },
        "eventos_clave": {
            nombre: eventos.get(nombre, 0)
            for nombre in ("modelo_respaldo_usado", "fallo_a2a", "accion_bloqueada",
                           "solicitud_bloqueada", "llamada_mcp", "rag_fragmentos",
                           "aprobacion_pendiente", "error_router")
        },
    }
