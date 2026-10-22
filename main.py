from chatbot import ChatBot

SALIDAS = {"salir", "exit", "quit"}


def main():
    bot = ChatBot()
    print("Chatbot listo. Escribí 'salir' para terminar.\n")

    while True:
        try:
            mensaje = input("Vos: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: ¡Hasta luego!")
            break

        if mensaje.lower() in SALIDAS:
            print("Bot: ¡Hasta luego!")
            break

        print(f"Bot: {bot.responder(mensaje)}\n")


if __name__ == "__main__":
    main()