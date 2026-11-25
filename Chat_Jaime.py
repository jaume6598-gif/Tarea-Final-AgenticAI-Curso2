
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agentes.jaime.agente import crear_agente_jaime

# Cargar configuración y construir el agente
load_dotenv()
agente = crear_agente_jaime()

# Historial de la conversación
historial = []

print("=== CHAT CON JAIME ===")
print("Escribe 'salir' para terminar.\n")

while True:
    pregunta = input("\nTú: ").strip()

    if pregunta.lower() == "salir":
        print("Chat finalizado.")
        break

    if not pregunta:
        continue

    try:
        resultado = agente.invoke(
            {"messages": historial + [HumanMessage(content=pregunta)]},
            config={"recursion_limit": 12}
        )

        nuevos = resultado["messages"][len(historial):]

        # Mostrar actividad de herramientas
        for mensaje in nuevos:
            if isinstance(mensaje, AIMessage) and mensaje.tool_calls:
                for llamada in mensaje.tool_calls:
                    print(f"[Herramienta solicitada: {llamada['name']}]")

            if isinstance(mensaje, ToolMessage):
                print(f"[Resultado herramienta: {str(mensaje.content)[:250]}]")

        # Mostrar respuesta final
        for mensaje in reversed(nuevos):
            if isinstance(mensaje, AIMessage) and not mensaje.tool_calls:
                print(f"\nJaime: {mensaje.content}")
                break

        # Conservar historial de la sesión
        historial = resultado["messages"]

    except Exception as error:
        print(f"Error durante la consulta: {type(error).__name__}")
        print("No se obtuvo una respuesta válida.")
