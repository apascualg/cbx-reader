#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBX Reader - Lector de cómics CBZ, CBR, ZIP y carpetas de imágenes
con herramienta de recorte (crop) y copia al portapapeles.

Tema estético:
  - Fondo: #191301
  - Texto y acentos: #F5B900
  - Tipografía: Inter (cargada dinámicamente)
  - Botones y cajas redondeadas anti-aliased
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
import zipfile
import io
import os
import sys
import ctypes
from pathlib import Path
from PIL import Image, ImageDraw, ImageTk, ImageEnhance

# ── Carga Dinámica de Fuente Inter ─────────────────────────
def load_inter_font():
    """Carga la fuente Inter.ttf en la sesión de Windows si está disponible."""
    try:
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_dir, 'Inter.ttf')
        if os.path.exists(font_path):
            FR_PRIVATE = 0x10
            ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
    except Exception:
        pass

load_inter_font()

# ── Soporte CBR (RAR) ──────────────────────────────────────
try:
    import rarfile
    CBR_AVAILABLE = True
    for _candidate in [
        r"C:\Program Files\WinRAR\UnRAR.exe",
        r"C:\Program Files (x86)\WinRAR\UnRAR.exe",
        r"C:\Program Files\WinRAR\WinRAR.exe",
        r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
        "unrar",
    ]:
        if os.path.exists(_candidate) or _candidate == "unrar":
            rarfile.UNRAR_TOOL = _candidate
            break
except ImportError:
    CBR_AVAILABLE = False

# ── Portapapeles Windows ───────────────────────────────────
import win32clipboard, win32con

def copy_image_to_clipboard(pil_image: Image.Image):
    """Copia una imagen PIL al portapapeles de Windows como DIB."""
    buf = io.BytesIO()
    pil_image.convert("RGB").save(buf, "BMP")
    dib = buf.getvalue()[14:]  # DIB = BMP sin la cabecera de 14 bytes
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, dib)
    finally:
        win32clipboard.CloseClipboard()


# ── Utilidades de Ordenación y Formatos ────────────────────
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}

def _natural_sort_key(s: str):
    import re
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(s))]

def filter_and_sort_pages(names):
    """Filtra archivos que no sean imágenes y descarta metadatos de macOS o archivos ocultos."""
    valid = []
    for n in names:
        p = Path(n)
        if any(part.startswith(".") or part == "__MACOSX" for part in p.parts):
            continue
        if p.suffix.lower() in IMAGE_EXTS:
            valid.append(n)
    return sorted(valid, key=_natural_sort_key)


# ── Gestor de Origen (Archivos Comprimidos o Carpetas) ─────
class ComicSource:
    """Maneja la lectura transparente desde CBZ, ZIP, CBR, RAR o carpetas con imágenes."""

    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self._zip = None
        self._rar = None
        self._is_folder = False
        self.pages: list[str] = []
        self.display_name = os.path.basename(self.path) or self.path
        self.initial_page_index = 0

        if os.path.isdir(self.path):
            self._is_folder = True
            found = []
            for root, dirs, files in os.walk(self.path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    if not f.startswith(".") and Path(f).suffix.lower() in IMAGE_EXTS:
                        found.append(os.path.join(root, f))
            self.pages = sorted(found, key=_natural_sort_key)
            if not self.pages:
                raise ValueError(f"No se encontraron imágenes en la carpeta:\n{self.display_name}")

        elif os.path.isfile(self.path):
            ext = Path(self.path).suffix.lower()

            if ext in IMAGE_EXTS:
                folder = os.path.dirname(self.path)
                self._is_folder = True
                self.display_name = os.path.basename(folder) or folder
                found = []
                for f in os.listdir(folder):
                    fp = os.path.join(folder, f)
                    if os.path.isfile(fp) and not f.startswith(".") and Path(f).suffix.lower() in IMAGE_EXTS:
                        found.append(fp)
                self.pages = sorted(found, key=_natural_sort_key)
                if self.path in self.pages:
                    self.initial_page_index = self.pages.index(self.path)
                return

            elif ext in (".cbz", ".zip"):
                self._zip = zipfile.ZipFile(self.path, "r")
                self.pages = filter_and_sort_pages(self._zip.namelist())
                if not self.pages:
                    raise ValueError(f"El archivo {ext} no contiene imágenes válidas.")

            elif ext in (".cbr", ".rar"):
                if not CBR_AVAILABLE:
                    raise RuntimeError("Instala 'rarfile' con: pip install rarfile")
                self._rar = rarfile.RarFile(self.path, "r")
                self.pages = filter_and_sort_pages(self._rar.namelist())
                if not self.pages:
                    raise ValueError(f"El archivo {ext} no contiene imágenes válidas.")
            else:
                raise ValueError(f"Formato no compatible: {ext}")
        else:
            raise FileNotFoundError(f"No se encontró el archivo o carpeta:\n{self.path}")

    def read_page(self, index: int) -> Image.Image:
        item = self.pages[index]
        if self._is_folder:
            return Image.open(item)
        elif self._zip:
            data = self._zip.read(item)
            return Image.open(io.BytesIO(data))
        elif self._rar:
            data = self._rar.read(item)
            return Image.open(io.BytesIO(data))
        raise RuntimeError("Fuente no disponible.")

    def get_page_filename(self, index: int) -> str:
        return Path(self.pages[index]).name

    def close(self):
        if self._zip:
            try: self._zip.close()
            except Exception: pass
            self._zip = None
        if self._rar:
            try: self._rar.close()
            except Exception: pass
            self._rar = None

    def __len__(self):
        return len(self.pages)


# ── Componentes UI Redondeados Estéticos ───────────────────
class RoundedButton(tk.Canvas):
    """Botón redondeado suave y anti-aliased con soporte de hover y estados."""

    def __init__(self, parent, text, command, font=None,
                 bg='#191301', fg='#F5B900',
                 box_bg='#281F05', hover_bg='#3D2F08', active_bg='#54410B',
                 border_color='#4E3A0B', border_width=1,
                 radius=8, padx=14, pady=6, min_width=0, tooltip=""):
        self.font = font or ('Inter', 9)
        self.text = text
        self.fg = fg
        self.bg_color = bg
        self.box_bg = box_bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg
        self.border_color = border_color
        self.border_width = border_width
        self.radius = radius
        self.padx = padx
        self.pady = pady
        self.command = command
        self._tooltip_text = tooltip

        tk_font = tkfont.Font(font=self.font)
        tw = tk_font.measure(text)
        th = tk_font.metrics('linespace')

        self.w = max(min_width, tw + padx * 2)
        self.h = th + pady * 2

        super().__init__(parent, width=self.w, height=self.h, bg=bg, highlightthickness=0, bd=0, cursor='hand2')

        self._img_normal = self._render_state(self.box_bg)
        self._img_hover = self._render_state(self.hover_bg)
        self._img_active = self._render_state(self.active_bg)

        self._bg_id = self.create_image(0, 0, anchor='nw', image=self._img_normal)
        self._text_id = self.create_text(self.w // 2, self.h // 2, text=self.text, fill=self.fg, font=self.font)

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<ButtonPress-1>', lambda e: self.itemconfig(self._bg_id, image=self._img_active))
        self.bind('<ButtonRelease-1>', self._on_release)

    def _on_enter(self, e):
        self.itemconfig(self._bg_id, image=self._img_hover)
        if hasattr(self, '_show_tt_func') and self._show_tt_func:
            self._show_tt_func(self)

    def _on_leave(self, e):
        self.itemconfig(self._bg_id, image=self._img_normal)
        if hasattr(self, '_hide_tt_func') and self._hide_tt_func:
            self._hide_tt_func()

    def _on_release(self, e):
        self.itemconfig(self._bg_id, image=self._img_hover)
        if self.command:
            self.command()

    def _render_state(self, fill_color):
        scale = 2
        sw, sh = self.w * scale, self.h * scale
        img = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        r = self.radius * scale
        bw = self.border_width * scale
        draw.rounded_rectangle([1, 1, sw - 2, sh - 2], radius=r, fill=fill_color, outline=self.border_color, width=bw)
        img = img.resize((self.w, self.h), Image.LANCZOS)
        return ImageTk.PhotoImage(img)


class RoundedBadge(tk.Canvas):
    """Caja redondeada decorativa para indicadores de estado, páginas y zoom."""

    def __init__(self, parent, text="", font=None,
                 bg='#191301', fg='#F5B900',
                 box_bg='#201803', border_color='#3D2E0B', border_width=1,
                 radius=8, padx=12, pady=6, min_width=50):
        self.font = font or ('Inter', 9)
        self.text = text
        self.fg = fg
        self.bg_color = bg
        self.box_bg = box_bg
        self.border_color = border_color
        self.border_width = border_width
        self.radius = radius
        self.padx = padx
        self.pady = pady
        self.min_width = min_width

        tk_font = tkfont.Font(font=self.font)
        tw = tk_font.measure(text)
        th = tk_font.metrics('linespace')
        self.w = max(min_width, tw + padx * 2)
        self.h = th + pady * 2

        super().__init__(parent, width=self.w, height=self.h, bg=bg, highlightthickness=0, bd=0)
        self._img = self._render_bg()
        self._bg_id = self.create_image(0, 0, anchor='nw', image=self._img)
        self._text_id = self.create_text(self.w // 2, self.h // 2, text=self.text, fill=self.fg, font=self.font)

    def set_text(self, new_text):
        if self.text == new_text:
            return
        self.text = new_text
        tk_font = tkfont.Font(font=self.font)
        tw = tk_font.measure(new_text)
        new_w = max(self.min_width, tw + self.padx * 2)
        if new_w != self.w:
            self.w = new_w
            self.config(width=self.w)
            self._img = self._render_bg()
            self.itemconfig(self._bg_id, image=self._img)
        self.coords(self._text_id, self.w // 2, self.h // 2)
        self.itemconfig(self._text_id, text=self.text)

    def _render_bg(self):
        scale = 2
        sw, sh = self.w * scale, self.h * scale
        img = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        r = self.radius * scale
        bw = self.border_width * scale
        draw.rounded_rectangle([1, 1, sw - 2, sh - 2], radius=r, fill=self.box_bg, outline=self.border_color, width=bw)
        img = img.resize((self.w, self.h), Image.LANCZOS)
        return ImageTk.PhotoImage(img)


# ── Aplicación Principal ───────────────────────────────────
class ReaderApp(tk.Tk):
    ZOOM_MIN = 0.05
    ZOOM_MAX = 8.0
    ZOOM_STEP = 1.15
    DARK_FACTOR = 0.28  # Brillo de la zona fuera del recorte

    # ── Paleta Estética Solicitada ──
    BG_COLOR     = "#191301"  # Fondo base oscuro cálido
    TEXT_COLOR   = "#F5B900"  # Texto ámbar/dorado cálido
    TEXT_MUTED   = "#D19F0D"  # Texto secundario dorado suave
    BORDER_COLOR = "#4A390C"  # Borde cálido de botones
    BTN_BG       = "#2B2005"  # Fondo botón en reposo
    BTN_HOVER    = "#3F2F08"  # Fondo botón al pasar cursor
    BTN_ACTIVE   = "#57420E"  # Fondo botón al hacer clic
    BADGE_BG     = "#201803"  # Fondo de cajas de estado / contadores
    BADGE_BORDER = "#3D2E0B"  # Borde de cajas de estado
    ACCENT       = "#F5B900"  # Acento dorado para marco de recorte

    def __init__(self):
        super().__init__()
        self.title("CBX Reader")
        self.configure(bg=self.BG_COLOR)
        self.geometry("1120x820")
        self.minsize(640, 420)

        # Determinar familia de fuente
        families = tkfont.families()
        self.font_family = "Inter" if "Inter" in families else "Segoe UI"
        self.font_main   = (self.font_family, 9)
        self.font_bold   = (self.font_family, 9, "bold")
        self.font_title  = (self.font_family, 16, "bold")
        self.font_small  = (self.font_family, 8)

        # Estado del documento
        self.archive: ComicSource | None = None
        self.current_page = 0
        self.zoom = 1.0
        self.fit_mode = True

        self._pil_image: Image.Image | None = None       # Imagen original
        self._displayed_image: Image.Image | None = None # Imagen escalada
        self._dark_base: Image.Image | None = None       # Caché oscurecida
        self._photo = None                               # Referencia Tk PhotoImage

        self._canvas_offset_x = 0
        self._canvas_offset_y = 0
        self._mid_drag_start = None  # Pan con botón central

        # Estado del recorte en coordenadas de la IMAGEN ORIGINAL
        self.crop_start_orig: tuple[int, int] | None = None
        self.crop_end_orig: tuple[int, int] | None = None
        self.crop_active = False
        self.crop_has_selection = False
        self.crop_rect_id = None

        self._tooltip_win = None

        self._build_ui()
        self._bind_events()

        # Icono de la ventana
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, 'icon.ico')
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Pantalla de bienvenida inicial
        self._render_welcome_screen()

        # Abrir archivo/carpeta pasado por línea de comandos si existe
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.after(100, lambda: self.load_source(sys.argv[1]))

    # ── Construcción de la UI ──────────────────────────────

    def _build_ui(self):
        # Barra superior (Toolbar)
        toolbar = tk.Frame(self, bg=self.BG_COLOR, pady=6)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10)

        def make_btn(parent, text, cmd, tooltip="", min_w=0):
            b = RoundedButton(
                parent, text=text, command=cmd, font=self.font_main,
                bg=self.BG_COLOR, fg=self.TEXT_COLOR,
                box_bg=self.BTN_BG, hover_bg=self.BTN_HOVER, active_bg=self.BTN_ACTIVE,
                border_color=self.BORDER_COLOR, min_width=min_w, tooltip=tooltip
            )
            b._show_tt_func = self._show_tooltip
            b._hide_tt_func = self._hide_tooltip
            return b

        def make_separator(parent):
            sep = tk.Frame(parent, bg="#332406", width=1, height=24)
            sep.pack(side=tk.LEFT, padx=6, pady=2)
            return sep

        # Grupo 1: Apertura
        self.btn_open_file = make_btn(toolbar, "📂 Archivo", self.open_file, "Abrir archivo CBZ, ZIP, CBR, RAR o imagen (Ctrl+O)")
        self.btn_open_file.pack(side=tk.LEFT, padx=(2, 3))

        self.btn_open_folder = make_btn(toolbar, "📁 Carpeta", self.open_folder, "Abrir carpeta con imágenes (Ctrl+D)")
        self.btn_open_folder.pack(side=tk.LEFT, padx=2)

        make_separator(toolbar)

        # Grupo 2: Navegación de páginas
        self.btn_prev = make_btn(toolbar, "◀ Anterior", self.prev_page, "Página anterior (← / A)")
        self.btn_prev.pack(side=tk.LEFT, padx=2)

        self.badge_page = RoundedBadge(
            toolbar, text="–", font=self.font_bold,
            bg=self.BG_COLOR, fg=self.TEXT_COLOR,
            box_bg=self.BADGE_BG, border_color=self.BADGE_BORDER, min_width=65
        )
        self.badge_page.pack(side=tk.LEFT, padx=3)

        self.btn_next = make_btn(toolbar, "Siguiente ▶", self.next_page, "Página siguiente (→ / D / Clic derecho)")
        self.btn_next.pack(side=tk.LEFT, padx=2)

        make_separator(toolbar)

        # Grupo 3: Zoom
        self.btn_zoom_out = make_btn(toolbar, "🔍-", self.zoom_out, "Alejar (-)", min_w=34)
        self.btn_zoom_out.pack(side=tk.LEFT, padx=2)

        self.badge_zoom = RoundedBadge(
            toolbar, text="100%", font=self.font_bold,
            bg=self.BG_COLOR, fg=self.TEXT_COLOR,
            box_bg=self.BADGE_BG, border_color=self.BADGE_BORDER, min_width=55
        )
        self.badge_zoom.pack(side=tk.LEFT, padx=3)

        self.btn_zoom_in = make_btn(toolbar, "🔍+", self.zoom_in, "Acercar (+)", min_w=34)
        self.btn_zoom_in.pack(side=tk.LEFT, padx=2)

        self.btn_fit = make_btn(toolbar, "⊡ Ajustar", self.fit_to_window, "Ajustar tamaño a ventana (F / 0)")
        self.btn_fit.pack(side=tk.LEFT, padx=(2, 6))

        make_separator(toolbar)

        # Estado / Mensajes en esquina superior derecha
        self.badge_status = RoundedBadge(
            toolbar, text="Listo", font=self.font_main,
            bg=self.BG_COLOR, fg=self.TEXT_MUTED,
            box_bg=self.BADGE_BG, border_color=self.BADGE_BORDER, min_width=90, padx=16
        )
        self.badge_status.pack(side=tk.RIGHT, padx=4)

        # Línea separadora decorativa bajo el toolbar
        hairline_top = tk.Frame(self, bg="#2B1F05", height=1)
        hairline_top.pack(side=tk.TOP, fill=tk.X)

        # Canvas central para cómic y recorte
        canvas_frame = tk.Frame(self, bg=self.BG_COLOR)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=self.BG_COLOR,
                                highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Línea separadora decorativa sobre la barra inferior
        hairline_bot = tk.Frame(self, bg="#2B1F05", height=1)
        hairline_bot.pack(side=tk.BOTTOM, fill=tk.X)

        # Barra de información inferior
        bottom_bar = tk.Frame(self, bg=self.BG_COLOR, height=28)
        bottom_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=3)

        self.badge_info = RoundedBadge(
            bottom_bar, text="Abre un archivo (CBZ, ZIP, CBR) o una carpeta con imágenes.",
            font=self.font_small, bg=self.BG_COLOR, fg=self.TEXT_MUTED,
            box_bg=self.BADGE_BG, border_color=self.BADGE_BORDER, padx=14, pady=3
        )
        self.badge_info.pack(side=tk.LEFT, padx=2)

    # ── Pantalla de Bienvenida ─────────────────────────────

    def _render_welcome_screen(self):
        """Muestra una tarjeta de bienvenida estética cuando no hay ningún cómic cargado."""
        if self.archive is not None:
            return
        self.canvas.delete("all")
        self.update_idletasks()
        cw = max(self.canvas.winfo_width(), 600)
        ch = max(self.canvas.winfo_height(), 400)

        card_w = min(560, cw - 40)
        card_h = 290
        cx = (cw - card_w) // 2
        cy = (ch - card_h) // 2

        # Dibujar tarjeta redondeada de bienvenida
        scale = 2
        img = Image.new('RGBA', (card_w * scale, card_h * scale), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([2, 2, card_w * scale - 4, card_h * scale - 4],
                               radius=16 * scale, fill="#211804", outline="#47360B", width=2 * scale)

        # Detalles interiores decorativos
        draw.rounded_rectangle([24 * scale, 180 * scale, (card_w - 24) * scale, (card_h - 20) * scale],
                               radius=10 * scale, fill="#191302", outline="#382A07", width=1 * scale)

        img = img.resize((card_w, card_h), Image.LANCZOS)
        self._welcome_img = ImageTk.PhotoImage(img)

        self.canvas.create_image(cx, cy, anchor='nw', image=self._welcome_img, tags="welcome")

        # Textos estilizados sobre la tarjeta
        mid_x = cx + card_w // 2
        self.canvas.create_text(mid_x, cy + 42, text="CBX  READER", fill=self.TEXT_COLOR,
                                font=self.font_title, tags="welcome")
        self.canvas.create_text(mid_x, cy + 72, text="Lector de cómics CBZ, CBR, ZIP y carpetas de imágenes",
                                fill=self.TEXT_MUTED, font=self.font_main, tags="welcome")

        self.canvas.create_text(mid_x, cy + 104, text="Usa los botones superiores 📂 Archivo o 📁 Carpeta para empezar",
                                fill="#ECC559", font=self.font_bold, tags="welcome")

        # Atajos rápidos dentro de la tarjeta
        shortcuts_text = (
            "✂ Clic izquierdo + arrastrar: Recortar viñeta\n"
            "🖱 Botón central del ratón: Mover la página (Pan)\n"
            "📋 Ctrl+C: Copiar recorte al portapapeles  ·  ↩ Ctrl+Z / Esc: Cancelar"
        )
        self.canvas.create_text(mid_x, cy + 232, text=shortcuts_text, fill=self.TEXT_MUTED,
                                font=self.font_small, justify="center", tags="welcome")

    # ── Eventos y Atajos ──────────────────────────────────

    def _bind_events(self):
        # Apertura
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-O>", lambda e: self.open_file())
        self.bind("<Control-d>", lambda e: self.open_folder())
        self.bind("<Control-D>", lambda e: self.open_folder())
        self.bind("<Control-Shift-O>", lambda e: self.open_folder())
        self.bind("<Control-Shift-o>", lambda e: self.open_folder())

        # Navegación
        self.bind("<Left>",      lambda e: self.prev_page())
        self.bind("<Right>",     lambda e: self.next_page())
        self.bind("<a>",         lambda e: self.prev_page())
        self.bind("<d>",         lambda e: self.next_page())

        # Zoom y ajuste
        self.bind("<plus>",      lambda e: self.zoom_in())
        self.bind("<equal>",     lambda e: self.zoom_in())
        self.bind("<minus>",     lambda e: self.zoom_out())
        self.bind("<0>",         lambda e: self.fit_to_window())
        self.bind("<f>",         lambda e: self.fit_to_window())

        # Deshacer / cancelar recorte
        self.bind("<Escape>",    lambda e: self._cancel_crop())
        self.bind("<Control-z>", lambda e: self._cancel_crop())
        self.bind("<Control-Z>", lambda e: self._cancel_crop())

        # Copiar y restablecer
        self.bind("<Control-c>", lambda e: self._copy_crop())
        self.bind("<Control-C>", lambda e: self._copy_crop())

        # Zoom con rueda del ratón
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>",   lambda e: self.zoom_in(cx=e.x, cy=e.y))
        self.canvas.bind("<Button-5>",   lambda e: self.zoom_out(cx=e.x, cy=e.y))

        # Clic izquierdo → recorte directo
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # Botón central → pan
        self.canvas.bind("<ButtonPress-2>",   self._on_mid_press)
        self.canvas.bind("<B2-Motion>",       self._on_mid_drag)
        self.canvas.bind("<ButtonRelease-2>", self._on_mid_release)

        # Clic derecho → página siguiente
        self.canvas.bind("<Button-3>", lambda e: self.next_page())

        self.canvas.bind("<Configure>", self._on_canvas_resize)

    # ── Conversión de Coordenadas ─────────────────────────

    def canvas_to_orig(self, cx: float, cy: float) -> tuple[int, int]:
        """Convierte coordenadas del canvas a píxeles de la imagen original."""
        if not self._pil_image or self.zoom <= 0:
            return 0, 0
        iw, ih = self._pil_image.size
        ox = self._canvas_offset_x
        oy = self._canvas_offset_y
        z = self.zoom

        ix = (cx - ox) / z
        iy = (cy - oy) / z

        ix = max(0.0, min(float(iw), ix))
        iy = max(0.0, min(float(ih), iy))
        return int(round(ix)), int(round(iy))

    def orig_to_canvas(self, ix: float, iy: float) -> tuple[float, float]:
        """Convierte coordenadas de la imagen original a coordenadas del canvas."""
        ox = self._canvas_offset_x
        oy = self._canvas_offset_y
        z = self.zoom
        return (ix * z + ox), (iy * z + oy)

    def _get_crop_orig_rect(self) -> tuple[int, int, int, int]:
        """Devuelve (x0, y0, x1, y1) ordenado en coordenadas de la imagen original."""
        if not self.crop_start_orig or not self.crop_end_orig:
            return 0, 0, 0, 0
        x0 = min(self.crop_start_orig[0], self.crop_end_orig[0])
        y0 = min(self.crop_start_orig[1], self.crop_end_orig[1])
        x1 = max(self.crop_start_orig[0], self.crop_end_orig[0])
        y1 = max(self.crop_start_orig[1], self.crop_end_orig[1])
        return x0, y0, x1, y1

    # ── Abrir Archivos / Carpetas ─────────────────────────

    def open_file(self):
        filetypes = [
            ("Archivos compatibles", "*.cbz *.zip *.cbr *.rar *.jpg *.jpeg *.png *.webp *.bmp"),
            ("Archivos ZIP / CBZ", "*.cbz *.zip"),
            ("Archivos RAR / CBR", "*.cbr *.rar"),
            ("Imágenes individuales", "*.jpg *.jpeg *.png *.webp *.bmp *.gif *.tiff"),
            ("Todos los archivos", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.load_source(path)

    def open_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta con imágenes")
        if folder:
            self.load_source(folder)

    def load_source(self, path: str):
        try:
            new_source = ComicSource(path)
            if self.archive:
                self.archive.close()
            self.archive = new_source
            self.current_page = getattr(new_source, "initial_page_index", 0)
            self.zoom = 1.0
            self.fit_mode = True
            self._cancel_crop()
            self.title(f"CBX Reader — {new_source.display_name}")
            self.canvas.delete("welcome")
            self._load_page()
        except Exception as ex:
            messagebox.showerror("Error al abrir", str(ex))

    # ── Navegación ────────────────────────────────────────

    def prev_page(self):
        if self.archive and self.current_page > 0:
            self.current_page -= 1
            self.fit_mode = True
            self._cancel_crop()
            self._load_page()

    def next_page(self):
        if self.archive and self.current_page < len(self.archive) - 1:
            self.current_page += 1
            self.fit_mode = True
            self._cancel_crop()
            self._load_page()

    def _load_page(self):
        if not self.archive:
            return
        try:
            self._pil_image = self.archive.read_page(self.current_page)
            self.badge_page.set_text(f"{self.current_page + 1} / {len(self.archive)}")
            fname = self.archive.get_page_filename(self.current_page)
            self.badge_info.set_text(
                f"  {fname}  ·  {self._pil_image.size[0]}×{self._pil_image.size[1]} px  ·  "
                f"Página {self.current_page + 1} de {len(self.archive)}  ·  "
                f"Clic izq. = recortar  ·  Botón central = mover (pan)  ·  Ctrl+C = copiar"
            )
            self._dark_base = None
            self.fit_to_window() if self.fit_mode else self._render_page()
        except Exception as ex:
            messagebox.showerror("Error al cargar página", str(ex))

    # ── Zoom ──────────────────────────────────────────────

    def zoom_in(self, event=None, cx=None, cy=None):
        if self._pil_image:
            self._apply_zoom(self.zoom * self.ZOOM_STEP, cx, cy)

    def zoom_out(self, event=None, cx=None, cy=None):
        if self._pil_image:
            self._apply_zoom(self.zoom / self.ZOOM_STEP, cx, cy)

    def _on_mousewheel(self, event):
        if self._pil_image:
            factor = self.ZOOM_STEP if event.delta > 0 else 1 / self.ZOOM_STEP
            self._apply_zoom(self.zoom * factor, event.x, event.y)

    def _apply_zoom(self, new_zoom, cx=None, cy=None):
        new_zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, new_zoom))
        if cx is not None and self._displayed_image:
            ratio = new_zoom / self.zoom
            self._canvas_offset_x = cx - ratio * (cx - self._canvas_offset_x)
            self._canvas_offset_y = cy - ratio * (cy - self._canvas_offset_y)
        self.zoom = new_zoom
        self.fit_mode = False

        self._render_page()
        if self.crop_has_selection or self.crop_active:
            self._update_crop_composite()
            self._update_crop_rect_coords()

    def fit_to_window(self):
        if not self._pil_image:
            return
        self.update_idletasks()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return
        iw, ih = self._pil_image.size
        self.zoom = min(cw / iw, ch / ih)
        self.fit_mode = True
        sw, sh = int(iw * self.zoom), int(ih * self.zoom)
        self._canvas_offset_x = (cw - sw) // 2
        self._canvas_offset_y = (ch - sh) // 2

        self._render_page()
        if self.crop_has_selection or self.crop_active:
            self._update_crop_composite()
            self._update_crop_rect_coords()

    # ── Renderizado ───────────────────────────────────────

    def _render_page(self):
        """Escala la imagen original y la muestra en el canvas."""
        if not self._pil_image:
            return
        iw, ih = self._pil_image.size
        sw = max(1, int(iw * self.zoom))
        sh = max(1, int(ih * self.zoom))
        resampler = Image.LANCZOS if self.zoom < 1.0 else Image.NEAREST
        self._displayed_image = self._pil_image.resize((sw, sh), resampler)
        self._dark_base = None
        self._put_image(self._displayed_image)
        self.badge_zoom.set_text(f"{int(self.zoom * 100)}%")

    def _put_image(self, img: Image.Image):
        """Envía una imagen PIL al canvas (crea o actualiza el elemento 'page')."""
        self._photo = ImageTk.PhotoImage(img)
        items = self.canvas.find_withtag("page")
        if items:
            self.canvas.itemconfig(items[0], image=self._photo)
            self.canvas.coords(items[0], self._canvas_offset_x, self._canvas_offset_y)
        else:
            self.canvas.create_image(
                self._canvas_offset_x, self._canvas_offset_y,
                anchor=tk.NW, image=self._photo, tags="page",
            )
        self.canvas.tag_lower("page")

    def _on_canvas_resize(self, event):
        if self.archive is None:
            self._render_welcome_screen()
        elif self._pil_image and self.fit_mode:
            self.after_idle(self.fit_to_window)
        elif self.crop_has_selection or self.crop_active:
            self._update_crop_rect_coords()

    # ── Pan con botón central ─────────────────────────────

    def _on_mid_press(self, event):
        if not self._pil_image:
            return
        self._mid_drag_start = (event.x, event.y, self._canvas_offset_x, self._canvas_offset_y)
        self.canvas.config(cursor="fleur")

    def _on_mid_drag(self, event):
        if not self._mid_drag_start:
            return
        dx = event.x - self._mid_drag_start[0]
        dy = event.y - self._mid_drag_start[1]
        self._canvas_offset_x = self._mid_drag_start[2] + dx
        self._canvas_offset_y = self._mid_drag_start[3] + dy

        self.canvas.coords("page", self._canvas_offset_x, self._canvas_offset_y)
        self._update_crop_rect_coords()

    def _on_mid_release(self, event):
        self._mid_drag_start = None
        self.canvas.config(cursor="crosshair")

    # ── Recorte (Crop) ────────────────────────────────────

    def _get_dark_base(self) -> Image.Image | None:
        """Calcula y almacena en caché la versión oscurecida de la imagen mostrada."""
        if self._dark_base is None and self._displayed_image is not None:
            rgb = self._displayed_image.convert("RGB")
            self._dark_base = ImageEnhance.Brightness(rgb).enhance(self.DARK_FACTOR)
        return self._dark_base

    def _update_crop_rect_coords(self):
        """Actualiza la posición del marco dorado en el canvas usando coordenadas de la imagen."""
        if not (self.crop_has_selection or self.crop_active):
            if self.crop_rect_id:
                self.canvas.delete(self.crop_rect_id)
                self.crop_rect_id = None
            return

        ox0, oy0, ox1, oy1 = self._get_crop_orig_rect()
        cx0, cy0 = self.orig_to_canvas(ox0, oy0)
        cx1, cy1 = self.orig_to_canvas(ox1, oy1)

        if self.crop_rect_id is None:
            self.crop_rect_id = self.canvas.create_rectangle(
                cx0, cy0, cx1, cy1,
                outline=self.ACCENT, width=2, dash=(6, 3), tags="crop_rect"
            )
        else:
            self.canvas.coords(self.crop_rect_id, cx0, cy0, cx1, cy1)
        self.canvas.tag_raise("crop_rect")

    def _update_crop_composite(self):
        """
        Genera la imagen compuesta:
          - Todo el fondo oscurecido
          - La zona seleccionada (en coordenadas fijas de la imagen) a brillo completo
        """
        if self._displayed_image is None:
            return

        dark = self._get_dark_base()
        if dark is None:
            return

        composite = dark.copy()

        if self.crop_has_selection or self.crop_active:
            ox0, oy0, ox1, oy1 = self._get_crop_orig_rect()
            z = self.zoom

            dx0 = int(round(ox0 * z))
            dy0 = int(round(oy0 * z))
            dx1 = int(round(ox1 * z))
            dy1 = int(round(oy1 * z))

            dw, dh = self._displayed_image.size
            dx0 = max(0, min(dw, dx0))
            dy0 = max(0, min(dh, dy0))
            dx1 = max(0, min(dw, dx1))
            dy1 = max(0, min(dh, dy1))

            if dx1 > dx0 and dy1 > dy0:
                bright_patch = self._displayed_image.crop((dx0, dy0, dx1, dy1))
                composite.paste(bright_patch, (dx0, dy0))

        self._put_image(composite)
        self._update_crop_rect_coords()

    def _on_press(self, event):
        """Clic izquierdo: inicia un nuevo recorte en la imagen."""
        if not self._pil_image:
            return
        ix, iy = self.canvas_to_orig(event.x, event.y)
        self.crop_start_orig = (ix, iy)
        self.crop_end_orig = (ix, iy)
        self.crop_active = True
        self.crop_has_selection = False

        self._update_crop_composite()
        self._update_status("Recortando…")

    def _on_drag(self, event):
        if self.crop_active:
            ix, iy = self.canvas_to_orig(event.x, event.y)
            self.crop_end_orig = (ix, iy)
            ox0, oy0, ox1, oy1 = self._get_crop_orig_rect()
            if (ox1 - ox0) > 4 and (oy1 - oy0) > 4:
                self.crop_has_selection = True
            self._update_crop_composite()

    def _on_release(self, event):
        if self.crop_active:
            self.crop_active = False
            ox0, oy0, ox1, oy1 = self._get_crop_orig_rect()
            if (ox1 - ox0) > 4 and (oy1 - oy0) > 4:
                self.crop_has_selection = True
                self._update_crop_composite()
                self._update_status("Ctrl+C para copiar")
            else:
                self._cancel_crop()

    def _cancel_crop(self):
        """Elimina la selección y restaura la visualización normal de la imagen."""
        self.crop_start_orig = None
        self.crop_end_orig = None
        self.crop_active = False
        self.crop_has_selection = False

        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None

        self._dark_base = None
        if self._displayed_image is not None:
            self._put_image(self._displayed_image)
        self._update_status("Listo")

    def _copy_crop(self):
        """Copia el área seleccionada al portapapeles y restablece la selección."""
        if not self.crop_has_selection or not self._pil_image:
            return

        ox0, oy0, ox1, oy1 = self._get_crop_orig_rect()
        w = ox1 - ox0
        h = oy1 - oy0

        if w < 2 or h < 2:
            self._update_status("Recorte pequeño")
            return

        cropped = self._pil_image.crop((ox0, oy0, ox1, oy1))
        try:
            copy_image_to_clipboard(cropped)
            self._cancel_crop()
            self._update_status("✔ Copiado")
            self.badge_info.set_text(f"✔ Recorte ({w}×{h} px) copiado al portapapeles. Pega con Ctrl+V")
        except Exception as ex:
            messagebox.showerror("Error al copiar", str(ex))

    # ── Estado y Tooltips ─────────────────────────────────

    def _update_status(self, msg: str):
        self.badge_status.set_text(msg)

    def _show_tooltip(self, widget):
        if not hasattr(widget, "_tooltip_text") or not widget._tooltip_text:
            return
        x = widget.winfo_rootx() + 15
        y = widget.winfo_rooty() + widget.winfo_height() + 6
        self._tooltip_win = tk.Toplevel(self)
        self._tooltip_win.wm_overrideredirect(True)
        self._tooltip_win.wm_geometry(f"+{x}+{y}")
        self._tooltip_win.configure(bg=self.BG_COLOR)

        tip_badge = RoundedBadge(
            self._tooltip_win, text=widget._tooltip_text, font=self.font_small,
            bg=self.BG_COLOR, fg=self.TEXT_COLOR,
            box_bg="#2A1F05", border_color=self.BORDER_COLOR, padx=10, pady=4
        )
        tip_badge.pack()

    def _hide_tooltip(self):
        if self._tooltip_win:
            self._tooltip_win.destroy()
            self._tooltip_win = None


# ── Entrada ───────────────────────────────────────────────
def main():
    app = ReaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
