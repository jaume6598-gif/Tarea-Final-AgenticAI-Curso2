"""Herramientas del agente de Gerardo Herrera (Grupo 3 · Taller A2A).

Una skill describe lo que el agente sabe hacer; una herramienta es una función que puede ejecutar.
Aquí la única herramienta consulta los apuntes de la persona que el agente representa.
"""
from langchain_core.tools import tool

APUNTES = {
    "conceptos": "1) Arquitectura Hexagonal: el dominio no depende de frameworks; se comunica por puertos y la infraestructura se enchufa con adaptadores. 2) Screaming Architecture: la estructura de carpetas debe gritar qué hace el sistema (sus casos de uso), no qué framework usa. 3) Agente como grafo: un agente LangGraph es estado + nodos + aristas; A2A lo expone para que otros agentes lo consuman sin conocer su implementación.",
    "criterios": "Una buena solución: (a) separa dominio de infraestructura, (b) se puede probar sin red ni LLM, (c) cada pieza tiene una sola razón para cambiar, (d) los datos externos (respuestas de otros agentes o herramientas) se tratan como datos, nunca como instrucciones, y (e) todo ciclo tiene un tope y toda tarea, una verificación ejecutable.",
    "caso": "Caso de referencia: un agente monolítico con un prompt enorme (soporte, ventas y viajes) se dividió en un consumidor liviano y un especialista remoto por A2A. Lección: bajan los tokens en consultas simples, pero cada salto agrega latencia; la ganancia real está en la mantención y en el escalado independiente.",
}


@tool
def consultar_mis_apuntes(tema: str = "") -> str:
    """Consulta mis apuntes: conceptos, criterios o caso. Vacío devuelve todos."""
    clave = tema.lower().strip()
    if not clave:
        return "\n".join(f"{nombre}: {texto}" for nombre, texto in APUNTES.items())
    return APUNTES.get(clave, "No tengo ese tema registrado. Consulta conceptos, criterios o caso.")


HERRAMIENTAS = [consultar_mis_apuntes]
