"""Repositorio del inventario de ejemplo.

Carga `datos/inventario.csv` en memoria al iniciar. Las acciones
autorizadas modifican solo la copia en memoria; el CSV es el dato
de ejemplo versionado y nunca se sobrescribe.
"""

import csv
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from threading import Lock

from config import obtener_config

RUTA_CSV = Path(__file__).with_name("inventario.csv")


@dataclass
class Lote:
    lote: str
    producto: str
    categoria: str
    proveedor: str
    stock: int
    stock_minimo: int
    vencimiento: str
    ubicacion: str
    despachado_a: list[str]

    def como_dict(self) -> dict:
        return asdict(self)


def _leer_csv(ruta: Path = RUTA_CSV) -> dict[str, Lote]:
    with ruta.open(encoding="utf-8") as archivo:
        return {
            fila["lote"]: Lote(
                lote=fila["lote"],
                producto=fila["producto"],
                categoria=fila["categoria"],
                proveedor=fila["proveedor"],
                stock=int(fila["stock"]),
                stock_minimo=int(fila["stock_minimo"]),
                vencimiento=fila["vencimiento"],
                ubicacion=fila["ubicacion"],
                despachado_a=[
                    local.strip()
                    for local in fila["despachado_a"].split(";")
                    if local.strip()
                ],
            )
            for fila in csv.DictReader(archivo)
        }


class Inventario:
    def __init__(self, lotes: dict[str, Lote]):
        self._lotes = lotes
        self._candado = Lock()

    @classmethod
    def desde_csv(cls, ruta: Path = RUTA_CSV) -> "Inventario":
        return cls(_leer_csv(ruta))

    def todos(self) -> list[Lote]:
        with self._candado:
            return deepcopy(list(self._lotes.values()))

    def obtener(self, codigo: str) -> Lote | None:
        with self._candado:
            lote = self._lotes.get(codigo.strip().upper())
            return deepcopy(lote) if lote else None

    def buscar_producto(self, texto: str) -> list[Lote]:
        termino = texto.strip().lower()
        return [
            lote for lote in self.todos()
            if termino in lote.producto.lower()
            or termino in lote.categoria.lower()
        ]

    def por_vencer(self, dias: int) -> list[Lote]:
        hoy = fecha_referencia()
        resultado = [
            lote for lote in self.todos()
            if 0 <= (date.fromisoformat(lote.vencimiento) - hoy).days <= dias
        ]
        return sorted(resultado, key=lambda lote: lote.vencimiento)

    def bajo_minimo(self) -> list[Lote]:
        return [lote for lote in self.todos() if lote.stock < lote.stock_minimo]

    def eliminar(self, codigo: str) -> bool:
        with self._candado:
            return self._lotes.pop(codigo.strip().upper(), None) is not None

    def reiniciar(self) -> None:
        with self._candado:
            self._lotes = _leer_csv()


def fecha_referencia() -> date:
    """Fecha 'hoy' de los datos de ejemplo (reproducible)."""
    return date.fromisoformat(obtener_config().fecha_referencia)


inventario = Inventario.desde_csv()
