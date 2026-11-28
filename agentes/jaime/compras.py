"""Encargo de reposicion para el Agente Compras (n8n) via A2A.

Los items se calculan de forma determinista desde el inventario y los
terminos de cada proveedor: el agente remoto recibe datos verificados,
no cifras generadas por el modelo.
"""

import json
from pathlib import Path

from datos.inventario import fecha_referencia, inventario

RUTA_PROVEEDORES = Path(__file__).resolve().parents[2] / "datos" / "proveedores.json"


def items_bajo_minimo() -> list[dict]:
    proveedores = json.loads(RUTA_PROVEEDORES.read_text(encoding="utf-8"))["proveedores"]
    items = []
    for lote in inventario.bajo_minimo():
        terminos = proveedores.get(lote.proveedor, {})
        items.append({
            "lote": lote.lote,
            "producto": lote.producto,
            "proveedor": lote.proveedor,
            "stock": lote.stock,
            "stock_minimo": lote.stock_minimo,
            "pedido_minimo": terminos.get("pedido_minimo_unidades", 0),
            "dias_entrega": terminos.get("dias_entrega", 0),
        })
    return items


def construir_encargo(items: list[dict]) -> str:
    datos = {"fecha_referencia": fecha_referencia().isoformat(), "items": items}
    return (
        "Soy el agente Jaime. Genera ordenes de compra en borrador para "
        "reponer estos items bajo stock minimo. Agrupa por proveedor y "
        "respeta el pedido minimo de cada uno.\n"
        f"```json\n{json.dumps(datos, ensure_ascii=False)}\n```"
    )
