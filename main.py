"""API publica: autenticacion, bitacora e invocacion del grafo de Jaime."""

import logging
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from agentes.errores import ErrorFlujo
from agentes.jaime.grafo import SIMULACIONES, grafo_jaime
from config import obtener_config, validar_config_api
from datos.inventario import inventario
from registro.bitacora import bitacora, evento
from registro.metricas import ContadorTokens, resumen
from seguridad.aprobaciones import ErrorAprobacion, aprobaciones
from seguridad.politicas import ALCANCE_ADMIN, ALCANCE_LECTOR, fijar_alcance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sistema_agentes")

config = obtener_config()
validar_config_api(config)

app = FastAPI(
    title="Tarea Final - Agentes Jaime y Gerardo",
    version="3.0.0",
    description=(
        "Jaime (router + worker ReAct) atiende solicitudes de operaciones "
        "de un minimarket y delega el diseno tecnologico a Gerardo por A2A."
    ),
)

cabecera_token = APIKeyHeader(name="X-API-Key", auto_error=False)


def _coincide(token: str, esperado: str) -> bool:
    return bool(esperado) and secrets.compare_digest(token, esperado)


def verificar_acceso(token: str | None = Depends(cabecera_token)) -> str:
    """Devuelve el alcance del token: 'admin' o 'lector'."""

    token = token or ""
    if _coincide(token, config.app_admin_token):
        return ALCANCE_ADMIN
    if _coincide(token, config.app_api_token):
        return ALCANCE_LECTOR
    raise HTTPException(status_code=401, detail="Acceso no autorizado")


class Consulta(BaseModel):
    pregunta: str = Field(min_length=5, max_length=2000)


def _simulacion(valor: str | None) -> str:
    valor = (valor or "").strip().lower()
    if not valor:
        return ""
    if not config.permitir_simulacion_fallos:
        raise HTTPException(
            status_code=400,
            detail="La simulacion de fallos esta deshabilitada en este entorno",
        )
    if valor not in SIMULACIONES:
        raise HTTPException(
            status_code=422,
            detail=f"X-Simular-Fallo debe ser uno de: {sorted(SIMULACIONES)}",
        )
    return valor


# ------------------------------------------------------------ endpoints

@app.get("/salud")
def comprobar_salud():
    return {
        "estado": "funcionando",
        "modelo": config.modelo,
        "modelo_respaldo": config.modelo_respaldo,
        "simulacion_fallos": config.permitir_simulacion_fallos,
    }


@app.post("/prueba-acceso")
def probar_acceso(consulta: Consulta, alcance: str = Depends(verificar_acceso)):
    return {
        "acceso": "autorizado",
        "alcance": alcance,
        "pregunta_recibida": consulta.pregunta,
    }


@app.post("/consultar")
async def consultar_agentes(
    consulta: Consulta,
    alcance: str = Depends(verificar_acceso),
    x_simular_fallo: Annotated[str | None, Header()] = None,
):
    simular = _simulacion(x_simular_fallo)
    pregunta = consulta.pregunta.strip()
    if len(pregunta) < 5:
        raise HTTPException(status_code=422, detail="La pregunta es demasiado corta")

    fijar_alcance(alcance)
    ejecucion = bitacora.iniciar(pregunta)
    evento("solicitud", alcance=alcance, simulacion=simular or None)

    try:
        resultado = await grafo_jaime.ainvoke(
            {"pregunta": pregunta, "simular": simular},
            config={"callbacks": [ContadorTokens()]},
        )
    except ErrorFlujo as error:
        bitacora.finalizar(ejecucion, "error", motivo=error.motivo,
                           codigo=error.codigo)
        return JSONResponse(status_code=error.codigo, content={
            "id_ejecucion": ejecucion.id_ejecucion,
            "estado": "error",
            "flujo": ejecucion.flujo,
            "detail": error.mensaje,
        })
    except Exception as error:
        logger.exception("Fallo no controlado en el grafo")
        bitacora.finalizar(ejecucion, "error", motivo=type(error).__name__,
                           codigo=500)
        return JSONResponse(status_code=500, content={
            "id_ejecucion": ejecucion.id_ejecucion,
            "estado": "error",
            "detail": "Error interno; revisa /registros con el id_ejecucion.",
        })

    ejecucion.flujo = resultado.get("flujo")
    estado = resultado.get("estado", "completado")
    bitacora.finalizar(ejecucion, estado)

    cuerpo = {
        "id_ejecucion": ejecucion.id_ejecucion,
        "estado": estado,
        "duracion_ms": ejecucion.duracion_ms,
        "uso": ejecucion.uso,
        "flujo": resultado.get("flujo"),
        "motivo": resultado.get("motivo"),
        "ruta": resultado.get("ruta", []),
        "respuesta": resultado.get("respuesta"),
        "traza": resultado.get("traza", []),
        **resultado.get("extra", {}),
    }
    if estado == "bloqueado":
        return JSONResponse(status_code=403, content=cuerpo)
    return cuerpo


@app.get("/registros")
def listar_registros(
    limite: int = Query(20, ge=1, le=200),
    _alcance: str = Depends(verificar_acceso),
):
    return [
        {
            "id_ejecucion": e.id_ejecucion,
            "inicio": e.inicio,
            "flujo": e.flujo,
            "estado": e.estado,
            "duracion_ms": e.duracion_ms,
        }
        for e in bitacora.listar(limite)
    ]


@app.get("/metricas")
def obtener_metricas(_alcance: str = Depends(verificar_acceso)):
    """Aggregated metrics over the executions kept in memory."""
    return resumen(bitacora)


@app.get("/registros/{id_ejecucion}")
def obtener_registro(id_ejecucion: str, _alcance: str = Depends(verificar_acceso)):
    ejecucion = bitacora.obtener(id_ejecucion)
    if ejecucion is None:
        raise HTTPException(status_code=404, detail="Ejecucion no encontrada")
    return ejecucion.como_dict()


class Decision(BaseModel):
    aprobar: bool
    comentario: str | None = Field(default=None, max_length=500)


@app.get("/aprobaciones")
def listar_aprobaciones(
    estado: str | None = Query(None, pattern="^(pendiente|aprobada|rechazada)$"),
    _alcance: str = Depends(verificar_acceso),
):
    return [s.como_dict() for s in aprobaciones.listar(estado)]


@app.post("/aprobaciones/{id_solicitud}")
def decidir_aprobacion(
    id_solicitud: str,
    decision: Decision,
    alcance: str = Depends(verificar_acceso),
):
    """Human-in-the-loop: only an administrator approves or rejects."""

    if alcance != ALCANCE_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Solo un administrador puede aprobar o rechazar mermas",
        )
    try:
        solicitud = aprobaciones.decidir(
            id_solicitud, decision.aprobar, responsable=ALCANCE_ADMIN,
            comentario=decision.comentario,
        )
    except ErrorAprobacion as error:
        raise HTTPException(status_code=409, detail=str(error))
    return solicitud.como_dict()


@app.get("/inventario/{lote}")
def consultar_lote(lote: str, _alcance: str = Depends(verificar_acceso)):
    encontrado = inventario.obtener(lote)
    if encontrado is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    return encontrado.como_dict()
