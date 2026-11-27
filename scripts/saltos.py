"""Muestra los saltos del grafo de Jaime para una pregunta.

Uso:
    python -m scripts.saltos "¿Qué productos vencen esta semana?"
    python -m scripts.saltos --diagrama
"""

import asyncio
import sys

from agentes.jaime.grafo import grafo_jaime
from registro.bitacora import bitacora


async def mostrar_saltos(pregunta: str) -> None:
    bitacora.iniciar(pregunta)
    saltos = 0
    async for actualizacion in grafo_jaime.astream(
        {"pregunta": pregunta, "simular": ""}, stream_mode="updates"
    ):
        for nodo, cambios in actualizacion.items():
            saltos += 1
            detalle = ""
            if cambios and cambios.get("flujo"):
                detalle = f" -> {cambios['flujo']} ({cambios.get('motivo', '')})"
            print(f"[{saltos}] {nodo}{detalle}")
            for paso in (cambios or {}).get("traza", []):
                print(f"      {paso}")
            if cambios and cambios.get("respuesta"):
                print(f"\nRespuesta ({cambios.get('estado')}):\n{cambios['respuesta']}")
    print(f"\nSaltos: {saltos}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--diagrama":
        print(grafo_jaime.get_graph().draw_mermaid())
    else:
        asyncio.run(mostrar_saltos(" ".join(sys.argv[1:])))
