import ctypes
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

from chatbot import ChatBot

# Evita que Windows desborde la ventana con zoom de pantalla
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ---------- Estilo (todo se cambia desde acá) ----------
SANS = "Segoe UI"
SERIF = "Georgia"

TEMAS = {
    "claro": {
        "fondo": "#f3efe8", "superficie": "#fbf9f5", "burbuja": "#e8e0d3",
        "tinta": "#2b2723", "suave": "#857c71", "linea": "#ddd6ca", "acento": "#8a5a44",
    },
    "oscuro": {
        "fondo": "#1c1a17", "superficie": "#25221e", "burbuja": "#312c26",
        "tinta": "#ece6dc", "suave": "#9a9084", "linea": "#37332d", "acento": "#c98f6e",
    },
}

SUGERENCIAS_INICIALES = ["Hola", "¿Qué podés hacer?", "Contame una curiosidad", "¿Qué hora es?"]

# Qué sugererencias
SIGUIENTES = {
    "saludo": ["¿Cómo estás?", "¿Qué podés hacer?", "Contame un chiste", "¿Qué hora es?"],
    "estado": ["Contame un chiste", "Contame una curiosidad", "¿Qué podés hacer?", "Estoy contento"],
    "nombre": ["¿Quién te hizo?", "¿Cómo funcionás?", "¿Para qué sirve esto?", "Me llamo Leandro"],
    "mi_nombre": ["Me llamo Leandro", "¿Qué podés hacer?", "Contame un chiste"],
    "nombre_guardado": ["Hola", "¿Cómo me llamo?", "Contame una curiosidad", "¿Qué hora es?"],
    "capacidades": ["¿Qué hora es?", "Cuánto es 12 por 4", "Contame un chiste", "Contame una curiosidad"],
    "proyecto": ["¿Cómo funcionás?", "¿Quién te hizo?", "¿Qué podés hacer?"],
    "creador": ["¿Cómo funcionás?", "¿Para qué sirve esto?", "Contame un chiste"],
    "funcionamiento": ["¿Quién te hizo?", "¿Para qué sirve esto?", "¿Qué podés hacer?"],
    "aburrido": ["Contame un chiste", "Contame una curiosidad", "Cuánto es 12 por 4"],
    "sueno": ["¿Qué hora es?", "Contame una curiosidad", "Chau"],
    "curioso": ["Otra curiosidad", "Contame un chiste", "Gracias", "¿Qué hora es?"],
    "triste": ["Contame un chiste", "Contame una curiosidad", "Gracias"],
    "contento": ["Contame un chiste", "Contame una curiosidad", "¿Qué podés hacer?"],
    "hora": ["¿Qué día es hoy?", "Contame un chiste", "Contame una curiosidad", "Gracias"],
    "fecha": ["¿Qué hora es?", "Contame un chiste", "Contame una curiosidad", "Gracias"],
    "elogio": ["Gracias", "Contame un chiste", "¿Qué podés hacer?"],
    "gracias": ["Contame un chiste", "Contame una curiosidad", "Chau"],
    "chiste": ["Otro chiste", "Contame una curiosidad", "¿Qué hora es?", "Gracias"],
    "despedida": ["Hola", "Contame un chiste", "¿Qué podés hacer?"],
    "calculo": ["Cuánto es 9 por 7", "100 entre 8", "¿Qué hora es?", "Contame un chiste"],
    "fallback": ["¿Qué podés hacer?", "Contame un chiste", "Contame una curiosidad", "Hola"],
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.bot = ChatBot()
        self.tema = "claro"
        self.sugerencias = list(SUGERENCIAS_INICIALES)
        self._reg = []        # widgets cuyo color depende del tema
        self._burbujas = []   # burbujas del usuario (cambian de color)
        self.historial = []   # Guardar la charla

        self.title("Asistente")
        self.geometry("640x740")
        self.minsize(480, 540)

        self._armar()
        self._aplicar_tema()
        self._bot("Hola. Soy un asistente, escribime lo que quieras.")

    @property
    def t(self):
        return TEMAS[self.tema]

    def _r(self, widget, **colores):
        """Registra un widget: colores = {opción_tk: clave_del_tema}."""
        self._reg.append((widget, colores))
        return widget

    # ---------- Construcción ----------
    def _armar(self):
        # Orden importa: lo de abajo se empaqueta primero para que nunca desaparezca
        pie = self._r(tk.Frame(self), bg="fondo")
        pie.pack(side="bottom", fill="x", padx=32, pady=(0, 24))

        self.caja = self._r(tk.Frame(pie, highlightthickness=1), bg="superficie")
        self.caja.pack(fill="x")

        self.campo = self._r(
            tk.Entry(self.caja, font=(SANS, 12), bd=0, highlightthickness=0),
            bg="superficie", fg="tinta", insertbackground="acento")
        self.campo.pack(side="left", fill="x", expand=True, padx=(16, 8), ipady=12)
        self.campo.bind("<Return>", lambda e: self._enviar())
        self.campo.bind("<FocusIn>", lambda e: self.caja.configure(highlightbackground=self.t["acento"]))
        self.campo.bind("<FocusOut>", lambda e: self.caja.configure(highlightbackground=self.t["linea"]))

        self.boton = self._r(
            tk.Label(self.caja, text="Enviar  →", font=(SANS, 10), padx=18, cursor="hand2"),
            bg="superficie", fg="acento")
        self.boton.pack(side="right", fill="y")
        self.boton.bind("<Button-1>", lambda e: self._enviar())
        self.boton.bind("<Enter>", lambda e: self.boton.configure(fg=self.t["tinta"]))
        self.boton.bind("<Leave>", lambda e: self.boton.configure(fg=self.t["acento"]))

        # Sugerencias
        self.zona_chips = self._r(tk.Frame(self), bg="fondo")
        self.zona_chips.pack(side="bottom", fill="x", padx=32, pady=(0, 14))

        # Encabezado
        cab = self._r(tk.Frame(self), bg="fondo")
        cab.pack(side="top", fill="x", padx=32, pady=(28, 0))

        izq = self._r(tk.Frame(cab), bg="fondo")
        izq.pack(side="left")
        self._r(tk.Label(izq, text="ASISTENTE", font=(SANS, 8, "bold")),
                bg="fondo", fg="suave").pack(anchor="w")
        self._r(tk.Label(izq, text="Nombre IA", font=(SERIF, 22, "italic")),
                bg="fondo", fg="tinta").pack(anchor="w", pady=(2, 16))

        der = self._r(tk.Frame(cab), bg="fondo")
        der.pack(side="right", anchor="n")
        self._boton_cab(der, "Limpiar", self._limpiar)
        self._boton_cab(der, "Guardar", self._guardar)
        self.btn_tema = self._boton_cab(der, "", self._cambiar_tema)

        self._r(tk.Frame(self, height=1), bg="linea").pack(side="top", fill="x", padx=32)

        # Conversación (ocupa lo que sobra)
        self.texto = self._r(
            tk.Text(self, wrap="word", state="disabled", bd=0, highlightthickness=0,
                    font=(SANS, 11), padx=32, pady=8, cursor="arrow"),
            bg="fondo", fg="tinta")
        self.texto.pack(side="top", fill="both", expand=True)

        self.campo.focus()

    def _boton_cab(self, padre, texto, comando):
        b = self._r(
            tk.Label(padre, text=texto, font=(SANS, 9), padx=12, pady=4,
                     cursor="hand2", highlightthickness=1),
            bg="fondo", fg="suave", highlightbackground="linea")
        b.pack(side="left", padx=(8, 0))
        b.bind("<Button-1>", lambda e: comando())
        b.bind("<Enter>", lambda e: b.configure(fg=self.t["acento"], highlightbackground=self.t["acento"]))
        b.bind("<Leave>", lambda e: b.configure(fg=self.t["suave"], highlightbackground=self.t["linea"]))
        return b

    # ---------- Tema ----------
    def _aplicar_tema(self):
        t = self.t
        self.configure(bg=t["fondo"])
        for widget, colores in self._reg:
            widget.configure(**{opcion: t[clave] for opcion, clave in colores.items()})

        self.caja.configure(highlightbackground=t["linea"], highlightcolor=t["acento"])
        self.btn_tema.configure(text="◐  Oscuro" if self.tema == "claro" else "◐  Claro")

        x = self.texto
        x.tag_configure("quien", font=(SANS, 8, "bold"), foreground=t["suave"], spacing1=22, spacing3=5)
        x.tag_configure("quien_yo", font=(SANS, 8, "bold"), foreground=t["suave"],
                        spacing1=22, spacing3=5, justify="right")
        x.tag_configure("bot", font=(SANS, 11), foreground=t["tinta"], rmargin=70, spacing2=5)
        x.tag_configure("linea_yo", justify="right")
        x.tag_configure("pensando", foreground=t["suave"])

        for b in self._burbujas:
            b.configure(bg=t["burbuja"], fg=t["tinta"], highlightbackground=t["linea"])

        self._dibujar_sugerencias()

    def _cambiar_tema(self):
        self.tema = "oscuro" if self.tema == "claro" else "claro"
        self._aplicar_tema()

    # ---------- Sugerencias ----------
    def _dibujar_sugerencias(self):
        for w in self.zona_chips.winfo_children():
            w.destroy()
        t = self.t
        for s in self.sugerencias:
            c = tk.Label(self.zona_chips, text=s, font=(SANS, 9), bg=t["fondo"], fg=t["suave"],
                         padx=12, pady=5, highlightthickness=1,
                         highlightbackground=t["linea"], cursor="hand2")
            c.pack(side="left", padx=(0, 8))
            c.bind("<Button-1>", lambda e, txt=s: self._enviar(txt))
            c.bind("<Enter>", lambda e, w=c: w.configure(
                fg=self.t["acento"], highlightbackground=self.t["acento"]))
            c.bind("<Leave>", lambda e, w=c: w.configure(
                fg=self.t["suave"], highlightbackground=self.t["linea"]))

    # ---------- Mensajes ----------
    def _bot(self, texto):
        self.historial.append(("Asistente", texto))
        self.texto.configure(state="normal")
        self.texto.insert("end", "ASISTENTE\n", "quien")
        self.texto.insert("end", texto + "\n", "bot")
        self.texto.configure(state="disabled")
        self.texto.see("end")

    def _yo(self, texto):
        self.historial.append(("Vos", texto))
        t = self.t
        self.texto.configure(state="normal")
        self.texto.insert("end", "VOS\n", "quien_yo")
        inicio = self.texto.index("end-1c")
        burbuja = tk.Label(self.texto, text=texto, font=(SANS, 11), bg=t["burbuja"], fg=t["tinta"],
                           justify="left", wraplength=360, padx=16, pady=10,
                           highlightthickness=1, highlightbackground=t["linea"])
        self._burbujas.append(burbuja)
        self.texto.window_create("end", window=burbuja)
        self.texto.insert("end", "\n")
        self.texto.tag_add("linea_yo", inicio, "end-1c")
        self.texto.configure(state="disabled")
        self.texto.see("end")

    def _pensando(self, activo):
        self.texto.configure(state="normal")
        if activo:
            self.texto.insert("end", "ASISTENTE\n", ("quien", "pensando"))
            self.texto.insert("end", "···\n", ("bot", "pensando"))
        else:
            rangos = self.texto.tag_ranges("pensando")
            if rangos:
                self.texto.delete(rangos[0], rangos[-1])
        self.texto.configure(state="disabled")
        self.texto.see("end")

    # ---------- Limpiar y guardar ----------
    def _limpiar(self):
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.configure(state="disabled")
        self._burbujas.clear()
        self.historial.clear()
        self.sugerencias = list(SUGERENCIAS_INICIALES)
        self._dibujar_sugerencias()
        self._bot("Hola. Soy un asistente, escribime lo que quieras.")
        self.campo.focus()

    def _guardar(self):
        if len(self.historial) <= 1:
            messagebox.showinfo("Guardar charla", "Todavía no hay nada para guardar.")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar charla",
            defaultextension=".txt",
            initialfile=f"charla_{datetime.now():%Y-%m-%d_%H-%M}.txt",
            filetypes=[("Texto", "*.txt")],
        )
        if not ruta:
            return
        lineas = [f"Charla guardada el {datetime.now():%d/%m/%Y a las %H:%M}", "-" * 40, ""]
        for quien, texto in self.historial:
            lineas += [f"{quien}: {texto}", ""]
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("\n".join(lineas))
        except OSError:
            messagebox.showerror("Guardar charla", "No se pudo guardar el archivo.")

    # ---------- Lógica ----------
    def _enviar(self, forzado=None):
        mensaje = (forzado if forzado is not None else self.campo.get()).strip()
        if not mensaje:
            return
        self.campo.delete(0, "end")
        self._yo(mensaje)
        self._pensando(True)

        def responder():
            self._pensando(False)
            self._bot(self.bot.responder(mensaje))
            self.sugerencias = SIGUIENTES.get(self.bot.ultimo_tag, SUGERENCIAS_INICIALES)
            self._dibujar_sugerencias()

        self.after(450, responder)
        self.campo.focus()


if __name__ == "__main__":
    App().mainloop()