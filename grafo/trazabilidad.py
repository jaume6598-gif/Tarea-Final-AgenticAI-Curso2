"""GraphRAG de trazabilidad sobre Neo4j.

Modelo del grafo (cargado por scripts/cargar_grafo.py):

    (Proveedor)-[:SUMINISTRA]->(Lote)-[:DE_PRODUCTO]->(Producto)-[:EN_CATEGORIA]->(Categoria)
    (Lote)-[:ALMACENADO_EN]->(Camara)
    (Lote)-[:DESPACHADO_A]->(Local)

La consulta es una plantilla Cypher fija y de solo lectura: el modelo
elige el tipo de punto de partida (proveedor, lote, camara o local) y
un valor, nunca escribe Cypher. El resultado incluye el recorrido de
relaciones que sustenta la respuesta.
"""

import logging
import os
import unicodedata
from datetime import date

from config import obtener_config
from datos.inventario import fecha_referencia
from registro.bitacora import evento

logger = logging.getLogger("sistema_agentes")

FILTROS = {
    "proveedor": "toLower(pr.nombre) CONTAINS $valor",
    "lote": "toLower(l.codigo) = $valor",
    "camara": "toLower(c.nombre) CONTAINS $valor",
    "local": ("EXISTS { MATCH (l)-[:DESPACHADO_A]->(x:Local) "
              "WHERE toLower(x.nombre) CONTAINS $valor }"),
}

PLANTILLA = """
MATCH (pr:Proveedor)-[:SUMINISTRA]->(l:Lote)-[:DE_PRODUCTO]->(p:Producto)
      -[:EN_CATEGORIA]->(cat:Categoria),
      (l)-[:ALMACENADO_EN]->(c:Camara)
WHERE {filtro}
OPTIONAL MATCH (l)-[:DESPACHADO_A]->(loc:Local)
RETURN pr.nombre AS proveedor, l.codigo AS lote, l.vencimiento AS vencimiento,
       l.stock AS stock, p.nombre AS producto, cat.nombre AS categoria,
       c.nombre AS camara, c.alerta AS alerta_camara, c.max_c AS max_c,
       collect(loc.nombre) AS locales
ORDER BY vencimiento
"""

LIMITE_FILAS = 50


class GrafoNoDisponible(RuntimeError):
    pass


def normalizar(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def crear_driver():
    config = obtener_config()
    if not config.neo4j_uri:
        raise GrafoNoDisponible("NEO4J_URI no configurada")
    import certifi
    from neo4j import GraphDatabase

    # Aura uses neo4j+s://; certifi avoids local CA-store issues.
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    return GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_usuario, config.neo4j_clave),
        connection_timeout=10,
    )


_driver = None


def ejecutar_lectura(cypher: str, parametros: dict) -> list[dict]:
    global _driver
    if _driver is None:
        _driver = crear_driver()
    registros, _, _ = _driver.execute_query(
        cypher, parametros, routing_="r", database_="neo4j"
    )
    return [registro.data() for registro in registros][:LIMITE_FILAS]


def consultar(tipo: str, valor: str, ejecutor=None) -> list[dict]:
    ejecutor = ejecutor or ejecutar_lectura
    tipo = tipo.strip().lower()
    if tipo not in FILTROS:
        raise ValueError(f"tipo debe ser uno de {sorted(FILTROS)}")
    cypher = PLANTILLA.format(filtro=FILTROS[tipo])
    return ejecutor(cypher, {"valor": normalizar(valor)})


def formatear(tipo: str, valor: str, filas: list[dict]) -> str:
    if not filas:
        return (f"SIN_RESULTADOS: el grafo no tiene lotes conectados a "
                f"{tipo} '{valor}'.")
    hoy = fecha_referencia()
    lineas = [f"Recorrido en el grafo desde {tipo} '{valor}' "
              f"({len(filas)} lotes conectados):"]
    for fila in filas:
        dias = (date.fromisoformat(str(fila["vencimiento"])) - hoy).days
        locales = ", ".join(sorted(fila["locales"])) or "sin despachos"
        alerta = " [CAMARA CON ALERTA DE TEMPERATURA]" if fila["alerta_camara"] else ""
        lineas.append(
            f"- Proveedor({fila['proveedor']}) -SUMINISTRA-> Lote({fila['lote']}) "
            f"-DE_PRODUCTO-> Producto({fila['producto']}) -EN_CATEGORIA-> "
            f"Categoria({fila['categoria']}); Lote({fila['lote']}) -ALMACENADO_EN-> "
            f"Camara({fila['camara']}){alerta}; Lote({fila['lote']}) -DESPACHADO_A-> "
            f"Local({locales}). Stock {fila['stock']}, vence {fila['vencimiento']} "
            f"(en {dias} dias)."
        )
    proveedores = sorted({f["proveedor"] for f in filas})
    locales = sorted({loc for f in filas for loc in f["locales"]})
    camaras = sorted({f["camara"] for f in filas})
    lineas.append(
        f"Hechos calculados sobre todo el recorrido: proveedores {proveedores}; "
        f"locales alcanzados {locales}; camaras {camaras}; "
        f"unidades en stock {sum(f['stock'] for f in filas)}."
    )
    return "\n".join(lineas)


def recorrer(tipo: str, valor: str, ejecutor=None) -> str:
    """Punto de entrada de la herramienta: nunca inventa si el grafo falla."""

    try:
        filas = consultar(tipo, valor, ejecutor)
    except ValueError as error:
        return f"Parametro invalido: {error}"
    except Exception as error:
        detalle = f"{type(error).__name__}: {' '.join(str(error).split())[:120]}"
        logger.warning("Grafo no disponible: %s", detalle)
        evento("grafo_no_disponible", detalle=detalle)
        return ("GRAFO_NO_DISPONIBLE: no se pudo consultar el grafo de "
                "trazabilidad. No hay recorrido que respalde una respuesta.")
    evento(
        "recorrido_grafo",
        tipo=tipo,
        valor=valor,
        lotes=[f["lote"] for f in filas],
        locales=sorted({loc for f in filas for loc in f["locales"]}),
        proveedores=sorted({f["proveedor"] for f in filas}),
    )
    return formatear(tipo, valor, filas)
