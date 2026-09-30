CALCULADORA
===========

Descripcion
-----------
Calculadora de escritorio escrita en Python con interfaz grafica. Admite las
operaciones +, -, *, /, %, ^, parentesis y cambio de signo. Muestra la expresion
en curso, guarda las ultimas 5 operaciones en un historial y avisa cuando la
expresion no es valida (por ejemplo, al dividir entre cero).

Ademas de la calculadora, el mismo archivo dibuja su propio icono y construye la
aplicacion de macOS "Calculadora.app", de modo que todo el proyecto se mantiene
en un unico archivo de codigo.


Libreria utilizada
------------------
Tkinter (libreria estandar de Python, incluida en el instalador).
Es la biblioteca que aporta los widgets de la interfaz: ventanas, botones,
cuadro de entrada, lista e historial.

Bibliotecas estandar de apoyo:
  ast        analiza y evalua la expresion de forma segura (no usa eval).
  operator   aplica las operaciones aritmeticas.
  tkinter.font  fuente del cuadro de entrada.
  math, struct, zlib   dibuja el icono y genera los archivos PNG.
  subprocess, shutil   arma y firma Calculadora.app.

En macOS se usan ademas las herramientas del sistema:
  iconutil   convierte el icono a formato .icns.
  codesign   firma la aplicacion para que macOS la ejecute sin avisos.


Requisitos
----------
Python 3.8 o superior con el modulo tkinter instalado.

En macOS se necesita ademas un Python con Tk 8.6 o superior, porque la version
8.5 que trae el sistema dibuja los botones de color blanco y oculta el texto.
Si tienes mas de un Python instalado, el lanzador busca el correcto solo.


Como ejecutarlo
---------------
python3 pract2_calc.py               Prepara Calculadora.app y abre la calculadora
python3 pract2_calc.py --icono       Vuelve a dibujar el icono
python3 pract2_calc.py --construir   Solo deja lista la aplicacion
python3 pract2_calc.py --sin-empaquetar   Solo abre la calculadora

Tambien se puede abrir Calculadora.app con doble clic desde el Finder.


Archivos del proyecto
---------------------
pract2_calc.py          Codigo fuente unico (calculadora + icono + empaquetado)
Calculadora.app         Aplicacion de macOS (se genera al ejecutar el script)
Calculadora.icns        Icono de la aplicacion (se genera al ejecutar el script)
Calculadora.iconset/    Icono en varios tamanos (se genera al ejecutar el script)


Notas tecnicas
--------------
- Las expresiones se validan con el modulo ast, nunca con eval, asi que no se
  puede ejecutar codigo arbitrario desde el teclado.
- Los botones se dibujan con tk.Label y no con tk.Button. En macOS, tk.Button
  ignora el color de fondo y respeta el del texto, por lo que un boton oscuro
  con texto blanco aparece blanco sobre blanco y no se ve.
- macOS no permite que una aplicacion ubicada en el Escritorio lea archivos de
  ~/Desktop. Por eso el codigo tambien se copia dentro de
  Calculadora.app/Contents/Resources/, y es la copia que usa la aplicacion.
