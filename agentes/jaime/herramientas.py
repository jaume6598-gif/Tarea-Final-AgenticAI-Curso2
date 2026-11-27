"""Herramientas del agente Jaime.

- consultar_mis_apuntes: conocimiento propio (conceptos, criterios, caso).
- consultar_stock / consultar_vencimientos: datos del inventario de ejemplo.
- eliminar_lote: accion con efecto real, protegida por politica.

Las herramientas capturan sus errores y responden texto: el agente
recibe el resultado como dato y decide si continua o responde.
"""

from langchain_core.tools import tool

from datos.inventario import fecha_referencia, inventario
from registro.bitacora import evento
from seguridad.politicas import MENSAJE_BLOQUEO, autorizar

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


def _linea(lote) -> str:
    return (
        f"{lote.lote} | {lote.producto} | stock {lote.stock} "
        f"(minimo {lote.stock_minimo}) | vence {lote.vencimiento} | "
        f"{lote.ubicacion} | proveedor {lote.proveedor}"
    )


@tool
def consultar_mis_apuntes(tema: str = "") -> str:
    """Consulta apuntes por tema. Si el tema no existe,
    devuelve todos los apuntes disponibles.
    Categorías: conceptos, criterios y caso.
    """

    clave = tema.lower().strip()

    if clave in APUNTES:
        return APUNTES[clave]

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


@tool
def consultar_stock(producto: str = "") -> str:
    """Consulta el stock por producto o categoria del inventario.
    Vacío devuelve los lotes bajo su stock minimo.
    Ejemplos: 'yogur', 'Lacteos', 'pan'.
    """

    if not producto.strip():
        lotes = inventario.bajo_minimo()
        if not lotes:
            return "Ningun lote esta bajo su stock minimo."
        return "Lotes bajo stock minimo:\n" + "\n".join(map(_linea, lotes))

    lotes = inventario.buscar_producto(producto)
    if not lotes:
        return f"No hay lotes que coincidan con '{producto}'."
    return "\n".join(map(_linea, lotes))


@tool
def consultar_vencimientos(dias: int = 7) -> str:
    """Lista los lotes que vencen dentro de los proximos `dias`
    (desde la fecha de referencia del inventario), ordenados FEFO.
    """

    dias = max(0, min(int(dias), 365))
    lotes = inventario.por_vencer(dias)
    hoy = fecha_referencia().isoformat()
    if not lotes:
        return f"Ningun lote vence en los proximos {dias} dias (hoy {hoy})."
    return (
        f"Lotes que vencen en {dias} dias (hoy {hoy}), orden FEFO:\n"
        + "\n".join(map(_linea, lotes))
    )


@tool
def buscar_procedimientos(consulta: str) -> str:
    """Busca en los documentos internos del minimarket (procedimiento
    FEFO, politica de mermas, plan HACCP de refrigerados) y devuelve los
    fragmentos relevantes con su fuente [archivo §seccion].
    Usala para preguntas sobre reglas, procedimientos o politicas.
    """

    from rag.documentos import formatear, obtener_buscador

    fragmentos, metodo = obtener_buscador().buscar(consulta)
    evento(
        "rag_fragmentos",
        consulta=consulta,
        metodo=metodo,
        fuentes=[f.cita for f in fragmentos],
        puntajes=[f.puntaje for f in fragmentos],
    )
    return formatear(fragmentos)


@tool
def registrar_merma(lote: str, cantidad: int, motivo: str) -> str:
    """Propone registrar una merma (vencimiento, daño, cadena de frio o
    diferencia de inventario). NO descuenta stock: crea una solicitud
    pendiente que un administrador debe aprobar.
    """

    from seguridad.aprobaciones import ErrorAprobacion, aprobaciones

    try:
        solicitud = aprobaciones.crear(lote, int(cantidad), motivo)
    except (ErrorAprobacion, ValueError) as error:
        return f"No se registro la merma: {error}"
    return (
        f"PENDIENTE_APROBACION: solicitud {solicitud.id} creada para "
        f"{solicitud.cantidad} unidades del lote {solicitud.lote} "
        f"({solicitud.motivo}). El stock NO cambia hasta que un "
        "administrador la apruebe."
    )


@tool
def eliminar_lote(lote: str) -> str:
    """Elimina un lote del inventario (accion con efecto real).
    Solo se ejecuta con acceso de administrador.
    """

    if not autorizar("eliminar_lote", lote=lote):
        return MENSAJE_BLOQUEO

    if inventario.eliminar(lote):
        evento("accion_ejecutada", accion="eliminar_lote", lote=lote)
        return f"Lote {lote} eliminado del inventario."
    return f"El lote {lote} no existe; no se realizo ningun cambio."


HERRAMIENTAS = [
    consultar_mis_apuntes,
    consultar_stock,
    consultar_vencimientos,
    buscar_procedimientos,
    registrar_merma,
    eliminar_lote,
]
