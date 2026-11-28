"""Shows the messages saved in Postgres for a conversation thread.

Proof for the persistent-memory extension: run it before and after
restarting the service and the same thread keeps its history.

Usage:
    python -m scripts.ver_memoria <hilo>
"""

import asyncio
import sys

from memoria import persistencia as memoria
from agentes.jaime.agente import crear_agente_jaime
from agentes.jaime.react import extraer_texto


async def mostrar(hilo: str) -> None:
    tipo = await memoria.iniciar()
    if tipo != "postgres":
        sys.exit(f"Postgres no disponible ({memoria.motivo()}).")
    agente = crear_agente_jaime(checkpointer=memoria.checkpointer())
    estado = await agente.aget_state({"configurable": {"thread_id": hilo}})
    mensajes = (estado.values or {}).get("messages", [])
    print(f"Hilo '{hilo}': {len(mensajes)} mensajes guardados en Postgres\n")
    for mensaje in mensajes:
        llamadas = getattr(mensaje, "tool_calls", None)
        texto = (f"llama a {[l['name'] for l in llamadas]}" if llamadas
                 else extraer_texto(mensaje.content)[:200].replace("\n", " "))
        print(f"- {mensaje.type:<5} {texto}")
    await memoria.cerrar()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(mostrar(sys.argv[1]))
