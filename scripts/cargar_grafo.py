"""Loads the traceability graph into Neo4j (idempotent: MERGE only).

Sources: datos/inventario.csv (lots, products, suppliers, stores,
cold rooms) and datos/proveedores.json (supplier terms and cold-room
temperature readings). Running it twice creates no duplicates.

Usage:
    python -m scripts.cargar_grafo
"""

import json
from pathlib import Path

from datos.inventario import Inventario
from grafo.trazabilidad import crear_driver

RAIZ = Path(__file__).resolve().parent.parent
LIMITE_C = 5.0

RESTRICCIONES = [
    "CREATE CONSTRAINT proveedor_nombre IF NOT EXISTS FOR (n:Proveedor) REQUIRE n.nombre IS UNIQUE",
    "CREATE CONSTRAINT lote_codigo IF NOT EXISTS FOR (n:Lote) REQUIRE n.codigo IS UNIQUE",
    "CREATE CONSTRAINT producto_nombre IF NOT EXISTS FOR (n:Producto) REQUIRE n.nombre IS UNIQUE",
    "CREATE CONSTRAINT categoria_nombre IF NOT EXISTS FOR (n:Categoria) REQUIRE n.nombre IS UNIQUE",
    "CREATE CONSTRAINT local_nombre IF NOT EXISTS FOR (n:Local) REQUIRE n.nombre IS UNIQUE",
    "CREATE CONSTRAINT ubicacion_nombre IF NOT EXISTS FOR (n:Ubicacion) REQUIRE n.nombre IS UNIQUE",
]

CARGAR_LOTE = """
MERGE (pr:Proveedor {nombre: $proveedor})
MERGE (l:Lote {codigo: $lote})
  SET l.vencimiento = $vencimiento, l.stock = $stock, l.stock_minimo = $stock_minimo
MERGE (p:Producto {nombre: $producto})
MERGE (cat:Categoria {nombre: $categoria})
MERGE (c:Ubicacion {nombre: $ubicacion})
MERGE (pr)-[:SUMINISTRA]->(l)
MERGE (l)-[:DE_PRODUCTO]->(p)
MERGE (p)-[:EN_CATEGORIA]->(cat)
MERGE (l)-[:ALMACENADO_EN]->(c)
WITH l
UNWIND $locales AS nombre_local
MERGE (loc:Local {nombre: nombre_local})
MERGE (l)-[:DESPACHADO_A]->(loc)
"""

ACTUALIZAR_PROVEEDOR = """
MATCH (pr:Proveedor {nombre: $nombre})
SET pr.dias_entrega = $dias_entrega, pr.pedido_minimo = $pedido_minimo
"""

ACTUALIZAR_CAMARA = """
MERGE (c:Ubicacion {nombre: $nombre})
SET c.max_c = $max_c, c.alerta = $max_c > $limite
"""


def main() -> None:
    datos = json.loads((RAIZ / "datos" / "proveedores.json").read_text(encoding="utf-8"))
    lotes = Inventario.desde_csv().todos()
    driver = crear_driver()
    with driver:
        driver.verify_connectivity()
        # v1 used the label Camara for every storage place (shelves too).
        driver.execute_query("MATCH (c:Camara) DETACH DELETE c")
        driver.execute_query("DROP CONSTRAINT camara_nombre IF EXISTS")
        for sentencia in RESTRICCIONES:
            driver.execute_query(sentencia)
        for lote in lotes:
            driver.execute_query(CARGAR_LOTE, {
                "proveedor": lote.proveedor, "lote": lote.lote,
                "vencimiento": lote.vencimiento, "stock": lote.stock,
                "stock_minimo": lote.stock_minimo, "producto": lote.producto,
                "categoria": lote.categoria, "ubicacion": lote.ubicacion,
                "locales": lote.despachado_a,
            })
        for nombre, info in datos["proveedores"].items():
            driver.execute_query(ACTUALIZAR_PROVEEDOR, {
                "nombre": nombre, "dias_entrega": info["dias_entrega"],
                "pedido_minimo": info["pedido_minimo_unidades"],
            })
        for nombre, lecturas in datos["temperaturas"].items():
            driver.execute_query(ACTUALIZAR_CAMARA, {
                "nombre": nombre, "max_c": max(l["c"] for l in lecturas),
                "limite": LIMITE_C,
            })
        conteo, _, _ = driver.execute_query(
            "MATCH (n) RETURN labels(n)[0] AS etiqueta, count(*) AS total "
            "ORDER BY etiqueta"
        )
        relaciones, _, _ = driver.execute_query(
            "MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS total ORDER BY tipo"
        )
    print("Nodos:", {r["etiqueta"]: r["total"] for r in conteo})
    print("Relaciones:", {r["tipo"]: r["total"] for r in relaciones})


if __name__ == "__main__":
    main()
