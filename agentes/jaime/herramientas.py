
"""Herramientas del agente Jaime Vidal (Grupo 3 · Taller A2A).

Permite consultar los apuntes del agente.
Si el tema solicitado no coincide con una categoría,
devuelve todos los apuntes disponibles.
"""

from langchain_core.tools import tool

APUNTES = {
    "conceptos": (
        "1) FEFO frente a FIFO: en alimentos sale primero "
        "lo que vence antes. "
        "2) HACCP: peligros, puntos críticos de control, "
        "límites, monitoreo y acciones correctivas. "
        "Inocuidad no es lo mismo que calidad. "
        "3) Indicadores de operación: OEE "
        "(disponibilidad × rendimiento × calidad), "
        "merma, rotación de inventario y OTIF."
    ),

    "criterios": (
        "Una buena solución: "
        "(a) primero la inocuidad, después el costo, "
        "(b) trazabilidad por lote, del proveedor al cliente, "
        "(c) cada mejora tiene un KPI y una meta, "
        "(d) un estándar escrito y el turno capacitado "
        "y (e) cadena de frío y rotación FEFO."
    ),

    "caso": (
        "Caso de referencia: una bodega con mermas por "
        "vencimiento ordenaba por fecha de llegada (FIFO). "
        "Se pasó a FEFO, con fecha de vencimiento visible, "
        "conteo cíclico semanal de los productos de alta "
        "rotación y una alerta de próximo a vencer para "
        "promocionar o donar. "
        "Lección: la merma se controla con disciplina "
        "diaria y un indicador a la vista."
    ),
}


@tool
def consultar_mis_apuntes(tema: str = "") -> str:
    """Consulta apuntes por tema. Si el tema no existe,
    devuelve todos los apuntes disponibles.
    Categorías: conceptos, criterios y caso.
    """

    clave = tema.lower().strip()

    # Si la categoría existe, devolver sus apuntes.
    if clave in APUNTES:
        return APUNTES[clave]

    # Si está vacía o no existe, devolver todos.
    contenido = "\n".join(
        f"{nombre}: {texto}"
        for nombre, texto in APUNTES.items()
    )

    if clave:
        return (
            f"No existe una categoría exacta para '{tema}'. "
            "Se entregan todos los apuntes disponibles:\n"
            + contenido
        )

    return contenido


HERRAMIENTAS = [consultar_mis_apuntes]
