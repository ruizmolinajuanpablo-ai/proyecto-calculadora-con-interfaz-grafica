"""Calculadora con evaluacion segura de expresiones.

Incluye el dibujo del icono y la construccion de Calculadora.app, de modo que
todo el programa vive en este unico archivo.

    python3 pract2_calc.py              actualiza el icono/.app y abre la calculadora
    python3 pract2_calc.py --icono      vuelve a dibujar el icono
    python3 pract2_calc.py --construir  solo prepara el icono y el .app
    python3 pract2_calc.py --sin-empaquetar   solo abre la calculadora
"""

import ast
import math
import operator
import os
import shutil
import struct
import subprocess
import sys
import tkinter as tk
import zlib
from functools import partial
from tkinter import font as tkfont

MAX_HISTORIAL = 5

FONDO = "#232339"
FONDO_PANEL = "#2c2c44"
FONDO_ENTRADA = "#15151f"
TEXTO = "#f4f4f6"
TEXTO_SUAVE = "#9a9ab0"
COLOR_ERROR = "#ff6b6b"
COLOR_OPERADOR = "#ff9f43"
COLOR_IGUAL = "#26c281"

OPERACIONES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

SIMBOLOS = "+-*/%"
ACCIONES = ("C", "(", ")", "±")

NOMBRE_APP = "Calculadora"
NOMBRE_ICNS = f"{NOMBRE_APP}.icns"
NOMBRE_ICONSET = f"{NOMBRE_APP}.iconset"
VERSION = "1.0"

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{nombre}</string>
    <key>CFBundleDisplayName</key>
    <string>{nombre}</string>
    <key>CFBundleExecutable</key>
    <string>{nombre}</string>
    <key>CFBundleIdentifier</key>
    <string>local.pract2.calculadora</string>
    <key>CFBundleIconFile</key>
    <string>{icono}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
"""

LANZADOR = """#!/bin/sh
# macOS no deja que una app del Escritorio lea ~/Desktop (privacidad TCC), asi
# que el codigo viaja dentro del bundle, en Contents/Resources/. Si el codigo de
# la carpeta se puede leer se usa ese; si no, la copia.

AQUI="$(cd "$(dirname "$0")" && pwd)"
COPIA="$AQUI/../Resources/{fuente}"
CARPETA="$(cd "$AQUI/../../.." && pwd -P)"
FUENTE="$CARPETA/{fuente}"

leible() {{ head -c 1 "$1" > /dev/null 2>&1; }}

if leible "$FUENTE"; then
  USAR="$FUENTE"
elif leible "$COPIA"; then
  USAR="$COPIA"
else
  echo "No se encontro el codigo de la calculadora." >&2
  echo "Se esperaba en $FUENTE o dentro de la app en $COPIA" >&2
  read -r -p "Pulsa Intro para cerrar..." _
  exit 1
fi

for CANDIDATO in "$CALCULADORA_PYTHON" /usr/local/bin/python3 /opt/homebrew/bin/python3 /usr/bin/python3 python3; do
  [ -n "$CANDIDATO" ] || continue
  case "$CANDIDATO" in
    */*) [ -x "$CANDIDATO" ] || continue ;;
  esac
  if "$CANDIDATO" -c "import tkinter, sys; sys.exit(0 if float(tkinter.TkVersion) >= 8.6 else 1)" > /dev/null 2>&1; then
    EJECUTABLE="$CANDIDATO"
    break
  fi
  EJECUTABLE=""
done

if [ -z "$EJECUTABLE" ]; then
  echo "No se encontro un Python 3 con tkinter 8.6 o superior." >&2
  echo "Descargalo de https://www.python.org/downloads/ e intentalo de nuevo." >&2
  read -r -p "Pulsa Intro para cerrar..." _
  exit 1
fi

exec "$EJECUTABLE" "$USAR" "$@"
"""

LIENZO = 1024
ICONO_SUPERIOR = (0x34, 0x34, 0x50)
ICONO_INFERIOR = (0x1B, 0x1B, 0x2E)
ICONO_PANTALLA = (0x15, 0x15, 0x1F)
ICONO_TEXTO = (0xF4, 0xF4, 0xF6)
ICONO_SUAVE = (0x9A, 0x9A, 0xB0)
ICONO_OPERADOR = (0xFF, 0x9F, 0x43)
ICONO_IGUAL = (0x26, 0xC2, 0x81)
ICONO_TECLA = (0x3D, 0x3D, 0x5C)

TAMANOS_ICONO = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]


def evaluar(expresion):
    def visitar(nodo):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
            return nodo.value
        if isinstance(nodo, ast.BinOp) and type(nodo.op) in OPERACIONES:
            return OPERACIONES[type(nodo.op)](visitar(nodo.left), visitar(nodo.right))
        if isinstance(nodo, ast.UnaryOp):
            valor = visitar(nodo.operand)
            if isinstance(nodo.op, ast.UAdd):
                return +valor
            if isinstance(nodo.op, ast.USub):
                return -valor
        raise ValueError("Expresión no permitida")

    return visitar(ast.parse(expresion, mode="eval").body)


def formatear(valor):
    if isinstance(valor, float):
        if valor.is_integer():
            return str(int(valor))
        return f"{valor:g}"
    return str(valor)


def presentar(texto):
    return texto.replace("*", "×").replace("/", "÷").replace("-", "−")


class Boton(tk.Label):
    """Botón dibujado con un Label.

    En macOS, tk.Button usa las APIs nativas de Aqua e ignora -background y
    -relief (el fondo queda blanco), pero sí respeta -foreground: un botón
    oscuro con texto blanco acaba blanco sobre blanco y el texto desaparece.
    Un Label lo dibuja Tk por completo, así que bg y fg se respetan en
    cualquier sistema operativo.
    """

    def __init__(self, padre, texto, comando, fondo, activo, fuente,
                 padx=10, pady=8):
        super().__init__(
            padre,
            text=texto,
            bg=fondo,
            fg=TEXTO,
            activebackground=activo,
            activeforeground=TEXTO,
            font=fuente,
            padx=padx,
            pady=pady,
            cursor="hand2",
            takefocus=False,
        )
        self.comando = comando
        self._fondo = fondo
        self._activo = activo
        self.bind("<Button-1>", self._pulsar)
        self.bind("<ButtonRelease-1>", self._soltar)
        self.bind("<Enter>", self._entrar)
        self.bind("<Leave>", self._salir)

    def _pulsar(self, evento):
        self.config(bg=self._activo)
        self.comando()

    def _soltar(self, evento):
        self.config(bg=self._activo)

    def _entrar(self, evento):
        self.config(bg=self._activo)
        return "break"

    def _salir(self, evento):
        self.config(bg=self._fondo)
        return "break"


class Calculadora(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora")
        self.resizable(False, False)
        self.configure(bg=FONDO)

        self.expresion = ""
        self.error = False
        self.recien_igual = False

        fuente = tkfont.nametofont("TkFixedFont").copy()
        fuente.configure(size=26)
        self.fuente_entrada = fuente

        self._construir()
        self._atajos()
        self._pintar()

    def _construir(self):
        marco = tk.Frame(self, bg=FONDO, padx=14, pady=14)
        marco.grid(row=0, column=0, sticky="nsew")

        self.entrada = tk.Entry(
            marco,
            justify="right",
            state="readonly",
            readonlybackground=FONDO_ENTRADA,
            fg=TEXTO,
            font=self.fuente_entrada,
            relief="flat",
            bd=0,
            highlightthickness=0,
            insertbackground=TEXTO,
        )
        self.entrada.grid(row=0, column=0, columnspan=2, sticky="sew", ipady=12, pady=(0, 6))

        self.estado = tk.Label(
            marco, text="", bg=FONDO, fg=COLOR_ERROR,
            font=("Helvetica", 10), anchor="w", height=1,
        )
        self.estado.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self._panel_historial(marco)
        self._panel_botones(marco)

    def _panel_historial(self, contenedor):
        panel = tk.LabelFrame(
            contenedor,
            text="  Historial ",
            bg=FONDO_PANEL,
            fg=TEXTO_SUAVE,
            font=("Helvetica", 10, "bold"),
            bd=0,
            highlightthickness=1,
            highlightbackground=FONDO_ENTRADA,
            padx=8,
            pady=8,
        )
        panel.grid(row=2, column=0, sticky="nsew", padx=(0, 10))

        self.historial = tk.Listbox(
            panel,
            width=24,
            height=MAX_HISTORIAL,
            bg=FONDO_PANEL,
            fg=TEXTO,
            font=("Helvetica", 11),
            relief="flat",
            highlightthickness=0,
            activestyle="none",
            selectbackground=FONDO_ENTRADA,
        )
        self.historial.pack(fill="both", expand=True)

        Boton(
            panel,
            texto="Limpiar historial",
            comando=self._limpiar_historial,
            fondo=FONDO_PANEL,
            activo=FONDO_ENTRADA,
            fuente=("Helvetica", 9),
        ).pack(fill="x", pady=(8, 0))

    def _panel_botones(self, contenedor):
        estilos = {
            "numero": (FONDO_PANEL, "#3d3d5c"),
            "operador": (COLOR_OPERADOR, "#ffb066"),
            "accion": (FONDO_PANEL, "#3d3d5c"),
            "igual": (COLOR_IGUAL, "#37dd9b"),
        }

        distribucion = [
            ("C", "C", "accion"), ("⌫", "⌫", "accion"),
            ("%", "%", "accion"), ("÷", "/", "operador"),
            ("7", "7", "numero"), ("8", "8", "numero"),
            ("9", "9", "numero"), ("×", "*", "operador"),
            ("4", "4", "numero"), ("5", "5", "numero"),
            ("6", "6", "numero"), ("−", "-", "operador"),
            ("1", "1", "numero"), ("2", "2", "numero"),
            ("3", "3", "numero"), ("+", "+", "operador"),
            ("0", "0", "numero"), (".", ".", "numero"),
            ("±", "±", "accion"), ("=", "=", "igual"),
        ]

        marco = tk.Frame(contenedor, bg=FONDO)
        marco.grid(row=2, column=1, sticky="nsew")
        for indice, (etiqueta, valor, estilo) in enumerate(distribucion):
            fila, columna = divmod(indice, 4)
            fondo, activo = estilos[estilo]
            boton = Boton(
                marco,
                texto=etiqueta,
                comando=partial(self._presionar, valor),
                fondo=fondo,
                activo=activo,
                fuente=("Helvetica", 17, "bold"),
            )
            boton.grid(
                row=fila, column=columna,
                padx=3, pady=3,
                sticky="nsew",
            )
            marco.columnconfigure(columna, weight=1, minsize=58)
            marco.rowconfigure(fila, weight=1, minsize=46)

    def _atajos(self):
        for tecla in "0123456789.+-*/()":
            self.bind(tecla, partial(self._presionar_tecla, tecla))
        self.bind("<Return>", self._igual)
        self.bind("<KP_Enter>", self._igual)
        self.bind("<Escape>", partial(self._presionar_tecla, "C"))
        self.bind("<BackSpace>", partial(self._presionar_tecla, "⌫"))

    def _presionar_tecla(self, tecla, evento):
        self._presionar(tecla)
        return "break"

    def _presionar(self, valor):
        if valor == "C":
            self.expresion = ""
            self.error = False
            self.recien_igual = False
            self._estado("")
        elif valor == "⌫":
            self.error = False
            self.expresion = self.expresion[:-1]
        elif valor == "=":
            self._igual()
            return
        elif valor == "±":
            self._cambiar_signo()
            return
        elif valor in ACCIONES:
            self._ingresar(valor)
        else:
            self._ingresar(valor)
        self._pintar()

    def _ingresar(self, caracter):
        actual = self.expresion
        if self.error or (self.recien_igual and caracter not in SIMBOLOS):
            actual = ""

        if actual == "-0" and (caracter.isdigit() or caracter == "."):
            actual = ""

        if caracter == ".":
            if not actual or actual[-1] in SIMBOLOS:
                actual += "0"
            elif actual[-1] == ".":
                return
        elif caracter in SIMBOLOS and actual and actual[-1] in SIMBOLOS:
            actual = actual[:-1] + caracter

        self.expresion = actual + caracter
        self.error = False
        self.recien_igual = False
        self._estado("")

    def _cambiar_signo(self):
        texto = self.expresion
        if not texto:
            self.expresion = "-0"
            self._pintar()
            return

        inicio = len(texto)
        while inicio > 0 and (texto[inicio - 1].isdigit() or texto[inicio - 1] == "."):
            inicio -= 1

        numero = texto[inicio:]
        if not numero or numero == ".":
            self._estado("No hay un número al final")
            return

        self.expresion = f"{texto[:inicio]}(-{numero})"
        self.error = False
        self.recien_igual = False
        self._estado("")
        self._pintar()

    def _igual(self, evento=None):
        expresion = self.expresion.rstrip(SIMBOLOS)
        if not expresion:
            return

        try:
            resultado = formatear(evaluar(expresion))
        except ZeroDivisionError:
            self._fallo("No se puede dividir entre cero")
            return
        except (SyntaxError, ValueError, TypeError, OverflowError):
            self._fallo("Expresión no válida")
            return

        self.historial.insert(0, f"{presentar(expresion)} = {resultado}")
        while self.historial.size() > MAX_HISTORIAL:
            self.historial.delete(self.historial.size() - 1)

        self.expresion = resultado
        self.error = False
        self.recien_igual = True
        self._estado("")
        self._pintar()

    def _fallo(self, mensaje):
        self.expresion = ""
        self.error = True
        self.recien_igual = False
        self._estado(mensaje)
        self._pintar()

    def _limpiar_historial(self):
        self.historial.delete(0, self.historial.size())

    def _estado(self, mensaje):
        self.estado.config(text=mensaje, fg=COLOR_ERROR if mensaje else TEXTO_SUAVE)

    def _pintar(self):
        self.entrada.configure(state="normal")
        self.entrada.delete(0, "end")
        self.entrada.insert(0, presentar(self.expresion) or "0")
        self.entrada.configure(state="readonly")


def escribir_png(ruta, ancho, alto, pixeles):
    filas = b"".join(
        b"\x00" + bytes(pixeles[y * ancho * 4:(y + 1) * ancho * 4])
        for y in range(alto)
    )

    def bloque(tipo, datos):
        cuerpo = tipo + datos
        crc = zlib.crc32(cuerpo) & 0xFFFFFFFF
        return struct.pack(">I", len(datos)) + cuerpo + struct.pack(">I", crc)

    cabecera = struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0)
    with open(ruta, "wb") as archivo:
        archivo.write(
            b"\x89PNG\r\n\x1a\n"
            + bloque(b"IHDR", cabecera)
            + bloque(b"IDAT", zlib.compress(filas, 9))
            + bloque(b"IEND", b"")
        )


def distancia_rectangulo(px, py, cx, cy, medio_ancho, medio_alto, radio):
    dx = abs(px - cx) - (medio_ancho - radio)
    dy = abs(py - cy) - (medio_alto - radio)
    fuera = math.hypot(max(dx, 0.0), max(dy, 0.0))
    dentro = min(max(dx, dy), 0.0)
    return fuera + dentro - radio


def mezclar(destino, indice, color, alfa):
    if alfa <= 0.0:
        return
    if alfa > 1.0:
        alfa = 1.0
    for k in range(3):
        previo = destino[indice + k] / 255.0
        destino[indice + k] = int(round((previo * (1.0 - alfa) + color[k] / 255.0 * alfa) * 255))
    if alfa >= 1.0:
        destino[indice + 3] = 255


def pintar_rectangulo(destino, paso, x0, y0, x1, y1, radio, color):
    total = LIENZO
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    medio_ancho = (x1 - x0) / 2.0
    medio_alto = (y1 - y0) / 2.0
    for py in range(int(y0) - 2, int(y1) + 3):
        if py < 0 or py >= total:
            continue
        for px in range(int(x0) - 2, int(x1) + 3):
            if px < 0 or px >= total:
                continue
            d = distancia_rectangulo(px, py, cx, cy, medio_ancho, medio_alto, radio)
            mezclar(destino, (py * total + px) * 4, color, min(max(0.5 - d, 0.0), 1.0))


def pintar_cuerpo(destino):
    total = LIENZO
    centro = LIENZO / 2.0
    medio = (LIENZO - 48) / 2.0
    for py in range(total):
        t = (py - 48.0) / (LIENZO - 96.0)
        color = tuple(
            int(round(ICONO_SUPERIOR[k] + (ICONO_INFERIOR[k] - ICONO_SUPERIOR[k]) * t))
            for k in range(3)
        )
        for px in range(total):
            d = distancia_rectangulo(px, py, centro, centro, medio, medio, 170.0)
            mezclar(destino, (py * total + px) * 4, color, min(max(0.5 - d, 0.0), 1.0))


def dibujar_icono():
    pixeles = bytearray(LIENZO * LIENZO * 4)

    pintar_cuerpo(pixeles)
    pintar_rectangulo(pixeles, 1.0, 128, 150, 896, 352, 30, ICONO_PANTALLA)
    pintar_rectangulo(pixeles, 1.0, 380, 216, 566, 274, 22, ICONO_TEXTO)
    pintar_rectangulo(pixeles, 1.0, 600, 216, 706, 274, 22, ICONO_OPERADOR)
    pintar_rectangulo(pixeles, 1.0, 740, 216, 866, 274, 22, ICONO_SUAVE)

    ancho_tecla = 172
    alto_tecla = 107
    separacion = 26
    for fila in range(4):
        for columna in range(4):
            x0 = 128 + columna * (ancho_tecla + separacion)
            y0 = 420 + fila * (alto_tecla + separacion)
            if fila == 3 and columna == 3:
                color = ICONO_IGUAL
            elif columna == 3:
                color = ICONO_OPERADOR
            else:
                color = ICONO_TECLA
            pintar_rectangulo(
                pixeles, 1.0,
                x0, y0, x0 + ancho_tecla, y0 + alto_tecla, 34, color,
            )

    return pixeles


def reducir(master, lado):
    if lado == LIENZO:
        return bytearray(master)
    factor = LIENZO // lado
    salida = bytearray(lado * lado * 4)
    for y in range(lado):
        base = y * factor
        for x in range(lado):
            r = g = b = a = 0
            for sy in range(factor):
                fila = (base + sy * factor) * 4
                for sx in range(factor):
                    origen = fila + (x * factor + sx) * 4
                    r += master[origen]
                    g += master[origen + 1]
                    b += master[origen + 2]
                    a += master[origen + 3]
            muestras = factor * factor
            destino = (y * lado + x) * 4
            salida[destino] = r // muestras
            salida[destino + 1] = g // muestras
            salida[destino + 2] = b // muestras
            salida[destino + 3] = a // muestras
    return salida


def generar_icono(carpeta):
    iconset = os.path.join(carpeta, NOMBRE_ICONSET)
    shutil.rmtree(iconset, ignore_errors=True)
    os.makedirs(iconset, exist_ok=True)

    master = dibujar_icono()
    for nombre, lado in TAMANOS_ICONO:
        escribir_png(os.path.join(iconset, nombre), lado, lado, reducir(master, lado))

    icns = os.path.join(carpeta, NOMBRE_ICNS)
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o", icns], check=True)
    return icns


def construir_app(carpeta, fuente, forzar_icono):
    app = os.path.join(carpeta, NOMBRE_APP + ".app")
    contenido = os.path.join(app, "Contents")
    ejecutable = os.path.join(contenido, "MacOS", NOMBRE_APP)
    recursos = os.path.join(contenido, "Resources")

    icns = os.path.join(carpeta, NOMBRE_ICNS)
    if forzar_icono or not os.path.exists(icns):
        if sys.platform == "darwin" and shutil.which("iconutil"):
            print("Dibujando el icono...")
            icns = generar_icono(carpeta)
        else:
            print("Icono omitido: iconutil solo existe en macOS.")

    os.makedirs(os.path.dirname(ejecutable), exist_ok=True)
    os.makedirs(recursos, exist_ok=True)

    with open(os.path.join(contenido, "Info.plist"), "w", encoding="utf-8") as archivo:
        archivo.write(INFO_PLIST.format(
            nombre=NOMBRE_APP, icono=NOMBRE_ICNS, version=VERSION,
        ))

    with open(ejecutable, "w", encoding="utf-8") as archivo:
        archivo.write(LANZADOR.format(
            nombre=NOMBRE_APP, fuente=os.path.basename(fuente),
        ))
    os.chmod(ejecutable, 0o755)

    shutil.copyfile(fuente, os.path.join(recursos, os.path.basename(fuente)))
    if os.path.exists(icns):
        shutil.copyfile(icns, os.path.join(recursos, NOMBRE_ICNS))

    if sys.platform == "darwin" and shutil.which("codesign"):
        subprocess.run(
            ["codesign", "--force", "--sign", "-", app],
            cwd=carpeta, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    return app


def desde_el_bundle():
    return os.sep + "Contents" + os.sep + "Resources" + os.sep in os.path.abspath(__file__)


def main():
    argumentos = sys.argv[1:]
    fuente = os.path.abspath(__file__)
    carpeta = os.path.dirname(fuente)

    if not desde_el_bundle() and "--sin-empaquetar" not in argumentos:
        try:
            app = construir_app(carpeta, fuente, "--icono" in argumentos)
            print(f"{os.path.basename(app)} lista.")
        except Exception as error:
            print(f"No se pudo preparar {NOMBRE_APP}.app: {error}")

    if "--construir" in argumentos:
        return

    Calculadora().mainloop()


if __name__ == "__main__":
    main()