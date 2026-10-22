import json
import random
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE = Path(__file__).parent
RUTA_INTENTS = BASE / "intents.json"
RUTA_LOG = BASE / "no_entendidos.txt"

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Una operación simple: "12 por 4", "10 + 5", "9 entre 3"
OPERACION = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*"
    r"(\+|-|\*|/|x|mas|menos|por|multiplicado por|entre|dividido por|dividido)\s*"
    r"(\d+(?:[.,]\d+)?)"
)
SIGNO = {
    "+": "+", "mas": "+",
    "-": "-", "menos": "-",
    "*": "*", "x": "*", "por": "*", "multiplicado por": "*",
    "/": "/", "entre": "/", "dividido": "/", "dividido por": "/",
}
NOMBRE = re.compile(
    r"(?:me llamo|mi nombre es)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{2,20})", re.IGNORECASE
)


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar de forma robusta."""
    texto = unicodedata.normalize("NFD", texto.lower().strip())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def formatear(n: float) -> str:
    if n == int(n):
        return str(int(n))
    return f"{n:.4f}".rstrip("0").rstrip(".").replace(".", ",")


class ChatBot:
    def __init__(self, ruta: Path = RUTA_INTENTS, umbral: float = 0.35,
                 umbral_sugerencia: float = 0.2):
        data = json.loads(Path(ruta).read_text(encoding="utf-8"))
        self.umbral = umbral
        self.umbral_sugerencia = umbral_sugerencia
        self.fallback = data["fallback"]
        self.respuestas = {i["tag"]: i["responses"] for i in data["intents"]}
        self.nombre = None  # se completa si el usuario dice "me llamo ..."
        self.ultimo_tag = None  # tema de la última respuesta (lo usa la interfaz)
        self.usadas = {}  # tag -> respuestas ya dadas (para no repetir)

        self.originales, patrones, self.etiquetas = [], [], []
        for intent in data["intents"]:
            for patron in intent["patterns"]:
                self.originales.append(patron)
                patrones.append(normalizar(patron))
                self.etiquetas.append(intent["tag"])

        # n-gramas de caracteres: tolera errores de tipeo ("holaa", "gracais")
        self.vectorizador = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self.matriz = self.vectorizador.fit_transform(patrones)

    # ---------- Respuestas dinámicas ----------
    def _rellenar(self, texto: str) -> str:
        ahora = datetime.now()
        fecha = f"{DIAS[ahora.weekday()]} {ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}"
        return (texto.replace("{hora}", ahora.strftime("%H:%M"))
                     .replace("{fecha}", fecha)
                     .replace("{nombre}", self.nombre or ""))

    def _sin_repetir(self, tag: str, opciones: list) -> str:
        """Recorre todas las opciones antes de repetir; nunca repite la última seguida."""
        usadas = self.usadas.setdefault(tag, [])
        libres = [r for r in opciones if r not in usadas]
        if not libres:
            ultima = usadas[-1] if usadas else None
            usadas.clear()
            libres = [r for r in opciones if r != ultima] or opciones
        eleccion = random.choice(libres)
        usadas.append(eleccion)
        return eleccion

    def _elegir(self, tag: str) -> str:
        if tag == "mi_nombre" and self.nombre:
            return f"Te llamás {self.nombre}."
        opciones = self.respuestas[tag]
        if not self.nombre:  # sin nombre, evitamos respuestas que lo usan
            opciones = [r for r in opciones if "{nombre}" not in r] or opciones
        return self._rellenar(self._sin_repetir(tag, opciones))

    def _calcular(self, texto: str):
        m = OPERACION.search(texto)
        if not m:
            return None
        a = float(m.group(1).replace(",", "."))
        b = float(m.group(3).replace(",", "."))
        signo = SIGNO[m.group(2)]
        if signo == "/" and b == 0:
            return "No se puede dividir por cero."
        resultado = {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b else 0}[signo]
        return f"El resultado es {formatear(resultado)}."

    def _recordar_nombre(self, mensaje: str):
        m = NOMBRE.search(mensaje)
        if not m:
            return None
        self.nombre = m.group(1).capitalize()
        return f"Un gusto, {self.nombre}. Ya me acordé de tu nombre."

    # ---------- Lo que no entiende ----------
    def _no_entendido(self, mensaje: str, mejor: int, similitud: float) -> str:
        try:
            with RUTA_LOG.open("a", encoding="utf-8") as f:
                f.write(f"{datetime.now():%Y-%m-%d %H:%M}\t{mensaje}\n")
        except OSError:
            pass
        if similitud >= self.umbral_sugerencia:
            return f"No estoy seguro de haber entendido. ¿Querías decir «{self.originales[mejor]}»?"
        return self._sin_repetir("fallback", self.fallback)

    # ---------- Punto de entrada ----------
    def responder(self, mensaje: str) -> str:
        if not mensaje.strip():
            self.ultimo_tag = "fallback"
            return random.choice(self.fallback)

        respuesta = self._recordar_nombre(mensaje)
        if respuesta:
            self.ultimo_tag = "nombre_guardado"
            return respuesta

        respuesta = self._calcular(normalizar(mensaje))
        if respuesta:
            self.ultimo_tag = "calculo"
            return respuesta

        vector = self.vectorizador.transform([normalizar(mensaje)])
        similitudes = cosine_similarity(vector, self.matriz)[0]
        mejor = int(similitudes.argmax())

        if similitudes[mejor] < self.umbral:
            self.ultimo_tag = "fallback"
            return self._no_entendido(mensaje, mejor, similitudes[mejor])

        self.ultimo_tag = self.etiquetas[mejor]
        return self._elegir(self.ultimo_tag)