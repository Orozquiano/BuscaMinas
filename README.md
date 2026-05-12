# Buscaminas (Python + Tkinter)

Juego clásico con interfaz actualizable al redimensionar la ventana (rejilla y tipografía se adaptan).

## Ubicación del proyecto

Todo el código y esta documentación están dentro de la carpeta **`minesweeper`**. La carpeta inmediatamente superior debe figurar en el path de Python como contenedora del paquete (por ejemplo `Proyecto Isa/minesweeper/` → ejecutas desde `Proyecto Isa`).

## Requisitos

- **Python 3.9 o superior** (recomendado 3.10+).
- **Tkinter** (interfaz gráfica; en muchos instaladores de Python ya viene incluido).

---

## Instalación (paso a paso)

### 1. Instalar Python

- **Windows:** descarga el instalador desde [python.org/downloads](https://www.python.org/downloads/) o Microsoft Store. Durante la instalación, marca la opción **“Add python.exe to PATH”** (añadir Python al PATH).
- **macOS:** suele incluirse Python 3 con Xcode Command Line Tools, o instálalo desde [python.org](https://www.python.org/downloads/macos/).
- **Linux:** instala el paquete de tu distribución, por ejemplo `sudo apt install python3 python3-pip` (Debian/Ubuntu).

Comprueba que funciona en una terminal:

```bash
python --version
```

Si en tu sistema el comando es `python3`:

```bash
python3 --version
```

### 2. Tkinter (obligatorio para la ventana del juego)

Tkinter viene con Python en **Windows** y en muchas instalaciones de **macOS**.

En **Linux**, a veces va en un paquete aparte:

```bash
# Debian / Ubuntu
sudo apt update
sudo apt install python3-tk
```

**Comprobar** que Tkinter está disponible:

```bash
python -c "import tkinter; print('Tkinter OK')"
```

Si falla, instala `python3-tk` (Linux) o reinstala Python en Windows marcando **tcl/tk** si el instalador lo ofrece.

### 3. Dependencias con pip (archivo `requirements.txt`)

Abre una terminal en la carpeta **`minesweeper`** (donde está `requirements.txt`) o indica la ruta completa al archivo.

```bash
cd ruta/a/tu/proyecto/minesweeper
pip install -r requirements.txt
```

*(En Linux/macOS puede ser `pip3` en lugar de `pip`.)*

Hoy el proyecto **no instala paquetes extra de PyPI**: el archivo documenta el comando y sirve para cuando se añadan librerías. El comando debería terminar sin errores aunque no descargue nada.

Si usas **entornos virtuales** (recomendado en proyectos grandes):

```bash
python -m venv .venv
```

- **Windows:** `.venv\Scripts\activate`
- **Linux/macOS:** `source .venv/bin/activate`

Luego:

```bash
pip install -r requirements.txt
```

---

## Cómo ejecutar

**Opción recomendada** (desde la carpeta **padre** de `minesweeper`, p. ej. `Proyecto Isa`):

```bash
python -m minesweeper
```

**Si ya estás dentro de** `minesweeper`:

```bash
python jugar.py
```

## Controles

| Acción | Control |
|--------|---------|
| Revelar | Clic izquierdo |
| Bandera | Clic derecho |
| Acorde (vecinos) | Clic central / rueda sobre número con banderas correctas |

**Números:** cada cifra indica **cuántas minas hay** en las 8 casillas alrededor (solo minas reales del tablero). Una **bandera en casilla vacía no cuenta**: si ves un `1` junto a una bandera y una mina, la bandera estaba equivocada. Al perder, el juego revela esas casillas mal marcadas para que veas el tablero real.

Menú **Juego**: niveles, personalizado, **F2** nueva partida.

## Estructura

```
minesweeper/
├── __init__.py
├── __main__.py      # python -m minesweeper
├── jugar.py         # python jugar.py (desde esta carpeta)
├── board.py         # Lógica del tablero
├── gui.py           # Interfaz
├── requirements.txt
└── README.md
```

## Licencia

Uso libre para aprendizaje y proyectos personales.
