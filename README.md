# Buscaminas (Python + Tkinter)

Juego clásico con interfaz actualizable al redimensionar la ventana (rejilla y tipografía se adaptan).

## Ubicación del proyecto

Todo el código y esta documentación están dentro de la carpeta **`minesweeper`**. La carpeta inmediatamente superior debe figurar en el path de Python como contenedora del paquete (por ejemplo `Proyecto Isa/minesweeper/` → ejecutas desde `Proyecto Isa`).

## Requisitos

- Python 3.9+ con **Tkinter** (en Windows suele venir instalado; en Debian/Ubuntu: `sudo apt install python3-tk`).

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
