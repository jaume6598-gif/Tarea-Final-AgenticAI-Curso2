"""Memoria persistente (checkpointer de LangGraph) y registro durable.

- Con DATABASE_URL: AsyncPostgresSaver (Neon). El hilo sobrevive a
  reinicios y redespliegues. Las ejecuciones de la bitacora tambien se
  guardan en la tabla `ejecuciones`, asi /registros/{id} funciona
  despues de un reinicio.
- Sin DATABASE_URL o si Postgres no responde: InMemorySaver (memoria
  'ram', se pierde al reiniciar) y se registra el motivo.
"""

import json
import logging

from langgraph.checkpoint.memory import InMemorySaver

from config import obtener_config

logger = logging.getLogger("sistema_agentes")

_estado: dict = {"checkpointer": None, "tipo": "ninguna", "pool": None,
                 "motivo": None}

SQL_TABLA = """
CREATE TABLE IF NOT EXISTS ejecuciones (
    id_ejecucion TEXT PRIMARY KEY,
    inicio TIMESTAMPTZ,
    flujo TEXT,
    estado TEXT,
    duracion_ms INTEGER,
    datos JSONB NOT NULL
)
"""

SQL_GUARDAR = """
INSERT INTO ejecuciones (id_ejecucion, inicio, flujo, estado, duracion_ms, datos)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (id_ejecucion) DO UPDATE
SET flujo = EXCLUDED.flujo, estado = EXCLUDED.estado,
    duracion_ms = EXCLUDED.duracion_ms, datos = EXCLUDED.datos
"""


async def iniciar() -> str:
    """Abre la memoria al iniciar la API. Devuelve 'postgres' o 'ram'."""

    url = obtener_config().database_url
    if url:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg.rows import dict_row
            from psycopg_pool import AsyncConnectionPool

            pool = AsyncConnectionPool(
                conninfo=url,
                min_size=1,
                max_size=2,
                open=False,
                check=AsyncConnectionPool.check_connection,
                kwargs={"autocommit": True, "prepare_threshold": 0,
                        "row_factory": dict_row},
            )
            await pool.open(wait=True, timeout=15)
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            async with pool.connection() as conexion:
                await conexion.execute(SQL_TABLA)
            _estado.update(checkpointer=checkpointer, tipo="postgres",
                           pool=pool, motivo=None)
            logger.info("Memoria persistente: postgres")
            return "postgres"
        except Exception as error:
            motivo = f"{type(error).__name__}: {' '.join(str(error).split())[:160]}"
            logger.warning("Postgres no disponible, se usa memoria RAM: %s", motivo)
            _estado["motivo"] = motivo
    else:
        _estado["motivo"] = "DATABASE_URL no configurada"

    _estado.update(checkpointer=InMemorySaver(), tipo="ram", pool=None)
    return "ram"


async def cerrar() -> None:
    if _estado["pool"] is not None:
        await _estado["pool"].close()
    _estado.update(checkpointer=None, tipo="ninguna", pool=None)


def checkpointer():
    return _estado["checkpointer"]


def tipo() -> str:
    return _estado["tipo"]


def motivo() -> str | None:
    return _estado["motivo"]


async def guardar_ejecucion(ejecucion) -> None:
    pool = _estado["pool"]
    if pool is None:
        return
    try:
        async with pool.connection() as conexion:
            await conexion.execute(SQL_GUARDAR, (
                ejecucion.id_ejecucion, ejecucion.inicio, ejecucion.flujo,
                ejecucion.estado, ejecucion.duracion_ms,
                json.dumps(ejecucion.como_dict(), ensure_ascii=False, default=str),
            ))
    except Exception as error:  # el registro durable nunca rompe la API
        logger.warning("No se pudo guardar la ejecucion: %s", type(error).__name__)


async def leer_ejecucion(id_ejecucion: str) -> dict | None:
    pool = _estado["pool"]
    if pool is None:
        return None
    try:
        async with pool.connection() as conexion:
            cursor = await conexion.execute(
                "SELECT datos FROM ejecuciones WHERE id_ejecucion = %s",
                (id_ejecucion,),
            )
            fila = await cursor.fetchone()
    except Exception as error:
        logger.warning("No se pudo leer la ejecucion: %s", type(error).__name__)
        return None
    return fila["datos"] if fila else None
