"""Boxhead Launcher - themed Tkinter GUI with secure auto-update."""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Ensure project root is on path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from launcher.config import LAUNCHER_VERSION
from launcher.updater import (
    get_local_version, compare_versions, fetch_latest_release,
    download_file, sha256_file, perform_update, is_game_running,
    launch_game,
)


def _chrome_dir():
    """Arayüz parçalarının klasörü; kaynaktan ve exe'den çalışmayı da kapsar.

    PyInstaller onefile'da veriler _MEIPASS altına açılır; exe'nin yanına
    elle konmuş bir klasör de kabul edilir.
    """
    rel = ('assets', 'ui', 'gothic', 'launcher')
    candidates = []
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidates.append(os.path.join(meipass, *rel))
        candidates.append(os.path.join(os.path.dirname(sys.executable), *rel))
    candidates.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), *rel))
    for path in candidates:
        if os.path.isdir(path):
            return path
    return candidates[0]


CHROME_DIR = _chrome_dir()

# tools/generate_launcher_chrome.py ile BİREBİR aynı olmalı; PNG'ler o
# ölçülerde hazır çizildiği için buradaki sayılar değişirse chrome yeniden
# üretilmeli.
TOPBAR_H = 40            # özel başlık çubuğu (OS çerçevesi kapalı)
CONTENT_H = 540          # bg.png yüksekliği; çubuğun ALTINA çizilir

# Yedek değerler. Gerçek yerleşim chrome ile birlikte üretilen layout.json'dan
# okunur; böylece PNG ölçüleri ile buradaki konumlar birbirinden kopamaz
# (bar iç genişliği tam olarak bu yüzden bir kez yanlış kalmıştı).
LAYOUT = {
    'content': (720, CONTENT_H),
    'window': (720, CONTENT_H + TOPBAR_H),
    'panel': (34, 132),
    'panel_inset': 52,
    'bar': (86, 256),
    'bar_inner': (40, 5, 468, 16),
    'btn_play': (34, 378, 318, 54),
    'btn_update': (368, 378, 318, 54),
    'btn_notes': (34, 444, 652, 54),
    'version_box': (490, 38, 196, 64),
}


def _load_layout():
    """layout.json varsa yerleşimi oradan alır (chrome ile aynı kaynak)."""
    path = os.path.join(CHROME_DIR, 'layout.json')
    layout = dict(LAYOUT)
    try:
        import json
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return layout, TOPBAR_H
    for key, value in data.items():
        layout[key] = tuple(value) if isinstance(value, list) else value
    return layout, int(data.get('topbar_h', TOPBAR_H))


class _IconButton:
    """Başlık çubuğu ikon butonu (kapat / küçült)."""

    def __init__(self, canvas, images, x, y, command, tooltip=None):
        self._c = canvas
        self._images = images
        self._command = command
        self._id = canvas.create_image(x, y, anchor='nw', image=images['normal'])
        canvas.tag_bind(self._id, '<Enter>', self._enter)
        canvas.tag_bind(self._id, '<Leave>', self._leave)
        canvas.tag_bind(self._id, '<ButtonRelease-1>', self._click)
        if tooltip:
            self._c.itemconfigure(self._id, tags=('icon', tooltip))

    def _enter(self, _e=None):
        self._c.itemconfigure(self._id, image=self._images['hover'])
        self._c.configure(cursor='hand2')

    def _leave(self, _e=None):
        self._c.itemconfigure(self._id, image=self._images['normal'])
        self._c.configure(cursor='')

    def _click(self, _e=None):
        if self._command:
            self._command()


class _CanvasText:
    """create_text öğesini tk.Label gibi .configure(text=, fg=) edilebilir yapar."""

    def __init__(self, canvas, item_id):
        self._c = canvas
        self._id = item_id

    def configure(self, text=None, fg=None, **_ignored):
        opts = {}
        if text is not None:
            opts['text'] = text
        if fg is not None:
            opts['fill'] = fg
        if opts:
            self._c.itemconfigure(self._id, **opts)

    config = configure


class _ImageButton:
    """Gotik plaka görselleriyle canvas butonu.

    tk.Button'un launcher'da kullanılan yüzeyini taklit eder (configure ile
    text/state/command, cget('state')), böylece güncelleme mantığı değişmiyor.
    """

    def __init__(self, canvas, images, box, text, command, font,
                 text_col='#f0eadc', disabled_col='#6b6558'):
        self._c = canvas
        self._images = images
        self._command = command
        self._state = tk.NORMAL
        self._hover = False
        self._pressed = False
        self._text_col = text_col
        self._disabled_col = disabled_col

        x, y, w, h = box
        self._img = canvas.create_image(x, y, anchor='nw', image=images['normal'])
        self._txt = canvas.create_text(x + w // 2, y + h // 2, text=text,
                                       fill=text_col, font=font)
        for item in (self._img, self._txt):
            canvas.tag_bind(item, '<Enter>', self._on_enter)
            canvas.tag_bind(item, '<Leave>', self._on_leave)
            canvas.tag_bind(item, '<ButtonPress-1>', self._on_press)
            canvas.tag_bind(item, '<ButtonRelease-1>', self._on_release)

    # --- görünüm ---
    def _refresh(self):
        if self._state == tk.DISABLED:
            key, col = 'disabled', self._disabled_col
        elif self._pressed:
            key, col = 'pressed', self._text_col
        elif self._hover:
            key, col = 'hover', self._text_col
        else:
            key, col = 'normal', self._text_col
        self._c.itemconfigure(self._img, image=self._images[key])
        self._c.itemconfigure(self._txt, fill=col)

    # --- olaylar ---
    def _on_enter(self, _e=None):
        self._hover = True
        if self._state != tk.DISABLED:
            self._c.configure(cursor='hand2')
        self._refresh()

    def _on_leave(self, _e=None):
        self._hover = False
        self._pressed = False
        self._c.configure(cursor='')
        self._refresh()

    def _on_press(self, _e=None):
        if self._state == tk.DISABLED:
            return
        self._pressed = True
        self._refresh()

    def _on_release(self, _e=None):
        was_pressed = self._pressed
        self._pressed = False
        self._refresh()
        if was_pressed and self._state != tk.DISABLED and self._command:
            self._command()

    # --- tk.Button uyumu ---
    def configure(self, text=None, state=None, command=None, **_ignored):
        if text is not None:
            self._c.itemconfigure(self._txt, text=text)
        if command is not None:
            self._command = command
        if state is not None:
            self._state = state
            if state == tk.DISABLED:
                self._pressed = False
        self._refresh()

    config = configure

    def cget(self, key):
        if key == 'state':
            return self._state
        raise KeyError(key)


class _ImageProgress:
    """bar_frame + dolgu görselinden ttk.Progressbar benzeri çubuk.

    Dolgu gerilmez, soldan kırpılır: Tk 8.6'nın `image copy -from` komutu
    kullanılır (Pillow gerekmez).
    """

    def __init__(self, canvas, pos, frame_img, fill_img, busy_img, inner):
        self._c = canvas
        self._x, self._y = pos
        self._fill = fill_img
        self._busy = busy_img
        self._dx, self._dy, self._w, self._h = inner
        canvas.create_image(self._x, self._y, anchor='nw', image=frame_img)
        self._item = canvas.create_image(self._x + self._dx, self._y + self._dy,
                                         anchor='nw')
        self._cur = None       # canlı PhotoImage referansı (GC koruması)
        self._chunk = None
        self._chunk_w = 0
        self._mode = 'determinate'
        self._value = 0.0
        self._max = 100.0
        self._anim = None
        self._interval = 60
        self._off = 0
        self._dir = 1
        self._last_w = None

    @staticmethod
    def _crop(src, width, height):
        width = max(1, int(width))
        out = tk.PhotoImage(width=width, height=height)
        out.tk.call(str(out), 'copy', str(src),
                    '-from', 0, 0, width, int(height))
        return out

    def _place(self, x_off):
        self._c.coords(self._item, self._x + self._dx + x_off, self._y + self._dy)

    def _render(self):
        ratio = self._value / self._max if self._max else 0.0
        width = int(self._w * max(0.0, min(1.0, ratio)))
        if width == self._last_w:
            return
        self._last_w = width
        if width <= 0:
            self._c.itemconfigure(self._item, image='')
            self._cur = None
            return
        self._cur = self._crop(self._fill, width, self._h)
        self._place(0)
        self._c.itemconfigure(self._item, image=self._cur)

    def _tick(self):
        span = max(1, self._w - self._chunk_w)
        self._off += self._dir * 10
        if self._off >= span:
            self._off, self._dir = span, -1
        elif self._off <= 0:
            self._off, self._dir = 0, 1
        self._place(self._off)
        self._anim = self._c.after(self._interval, self._tick)

    # --- ttk.Progressbar uyumu ---
    def configure(self, mode=None, value=None, maximum=None, **_ignored):
        if maximum is not None:
            self._max = float(maximum) or 100.0
        if mode is not None:
            self._mode = mode
        if value is not None:
            self._value = float(value)
        if self._mode == 'determinate':
            self._render()

    config = configure

    def start(self, interval=None):
        if interval:
            self._interval = max(20, int(interval) * 4)
        self.stop()
        self._mode = 'indeterminate'
        self._chunk_w = max(60, self._w // 4)
        self._chunk = self._crop(self._busy, self._chunk_w, self._h)
        self._cur = self._chunk
        self._off, self._dir, self._last_w = 0, 1, None
        self._c.itemconfigure(self._item, image=self._chunk)
        self._tick()

    def stop(self):
        if self._anim is not None:
            self._c.after_cancel(self._anim)
            self._anim = None
        self._chunk = None
        self._last_w = None


class LauncherApp:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.install_dir = os.path.dirname(sys.executable)
        else:
            self.install_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        os.chdir(self.install_dir)

        self.root = tk.Tk()
        self.root.title("Boxhead 2.0 — Launcher")
        self.root.geometry("720x540")
        self.root.resizable(False, False)
        self.root.configure(bg='#0d1018')

        self.release_info = None
        self._build_ui()
        self.root.after(100, self._check_updates)

    # --- tema paleti (oyunla ortak; bkz. ui_theme.COLORS) ---
    PALETTE = {
        'window': '#181416', 'panel': '#1a1822', 'panel_alt': '#141218',
        'border': '#7a7e86', 'text': '#f0eadc', 'muted': '#8c8470',
        'gold': '#966416', 'blue': '#1e4e6e', 'green': '#2c603a',
        'orange': '#b47a1e', 'red': '#92180f',
    }

    def _build_ui(self):
        """Gotik asset'lerle çizer; asset yoksa eski widget arayüzüne düşer."""
        self.colors = dict(self.PALETTE)
        try:
            self._build_ui_themed()
            return
        except Exception as error:  # eksik/bozuk PNG, eski Tk sürümü vb.
            print(f"[launcher] tema yuklenemedi, klasik arayuz: {error}")
            for child in self.root.winfo_children():
                child.destroy()
        self._build_ui_classic()

    def _load_chrome(self):
        """Gerekli PNG'leri yükler. Eksik olan varsa hata verir."""
        needed = ['bg.png', 'panel.png', 'version_box.png', 'bar.png',
                  'bar_fill.png', 'bar_fill_busy.png', 'titlebar.png',
                  'crest_small.png']
        for key in ('play', 'update', 'notes'):
            needed += [f'btn_{key}_{s}.png'
                       for s in ('normal', 'hover', 'pressed', 'disabled')]
        for key in ('close', 'min'):
            needed += [f'btn_{key}_{s}.png' for s in ('normal', 'hover')]

        images = {}
        for name in needed:
            path = os.path.join(CHROME_DIR, name)
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"{name} yok - 'python tools/generate_launcher_chrome.py' calistir")
            images[name] = tk.PhotoImage(file=path)
        return images

    def _build_ui_themed(self):
        LAYOUT_R, T = _load_layout()
        W, H = LAYOUT_R['window']
        c = self.colors

        # PhotoImage referanslari canli kalmali, yoksa Tk gorseli siler
        self._chrome = self._load_chrome()
        img = self._chrome

        # OS baslik cubugunu kaldir, pencereyi ekranda ortala
        self.root.overrideredirect(True)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{max(0, (sw - W) // 2)}+{max(0, (sh - H) // 3)}")
        self.root.configure(bg='#0b0a0d')

        canvas = tk.Canvas(self.root, width=W, height=H, highlightthickness=0,
                           bd=0, bg='#0b0a0d')
        canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas = canvas

        canvas.create_image(0, T, anchor='nw', image=img['bg.png'])

        # --- ozel baslik cubugu ---
        bar_bg = canvas.create_image(0, 0, anchor='nw', image=img['titlebar.png'])
        crest = canvas.create_image(16, T // 2, anchor='w', image=img['crest_small.png'])
        title = canvas.create_text(60, T // 2, anchor='w',
                                   text="BOXHEAD 2.0  —  LAUNCHER",
                                   fill='#cfc6b4', font=("Georgia", 10, "bold"))
        # Cubuk / baslik / süs: surukleyerek tasi
        for item in (bar_bg, title, crest):
            canvas.tag_bind(item, '<ButtonPress-1>', self._drag_start)
            canvas.tag_bind(item, '<B1-Motion>', self._drag_move)

        icon_y = (T - 26) // 2
        self.close_btn = _IconButton(
            canvas, {s: img[f'btn_close_{s}.png'] for s in ('normal', 'hover')},
            W - 38, icon_y, self._quit)
        self.min_btn = _IconButton(
            canvas, {s: img[f'btn_min_{s}.png'] for s in ('normal', 'hover')},
            W - 74, icon_y, self._minimize)

        # --- marka ---
        canvas.create_text(40, T + 46, anchor='w', text="NATIVE EVOLUTION",
                           fill='#4a86b4', font=("Georgia", 9, "bold"))
        canvas.create_text(38, T + 76, anchor='w', text="BOXHEAD 2.0",
                           fill=c['text'], font=("Georgia", 28, "bold"))
        canvas.create_text(40, T + 110, anchor='w',
                           text="Hayatta kal. Güçlen. Sınırları aş.",
                           fill=c['muted'], font=("Segoe UI", 10))

        vx, vy, vw, _vh = LAYOUT_R['version_box']
        canvas.create_image(vx, vy + T, anchor='nw', image=img['version_box.png'])
        self.version_label = _CanvasText(canvas, canvas.create_text(
            vx + vw // 2, vy + T + 32, text=(
                f"OYUN      v{get_local_version()}\n"
                f"LAUNCHER  v{LAUNCHER_VERSION}"),
            fill=c['muted'], font=("Consolas", 9, "bold"), justify=tk.CENTER))

        # --- durum karti ---
        px, py = LAYOUT_R['panel']
        py += T
        canvas.create_image(px, py, anchor='nw', image=img['panel.png'])
        ix = px + LAYOUT_R['panel_inset']
        iy = py + LAYOUT_R['panel_inset']

        self.status_dot = _CanvasText(canvas, canvas.create_text(
            ix + 4, iy + 12, anchor='w', text="●", fill=c['blue'],
            font=("Segoe UI", 12)))
        self.status_label = _CanvasText(canvas, canvas.create_text(
            ix + 24, iy + 12, anchor='w', text="Sürüm kontrol ediliyor",
            fill=c['text'], font=("Georgia", 15, "bold")))
        self.status_detail = _CanvasText(canvas, canvas.create_text(
            ix, iy + 38, anchor='nw', width=530,
            text="GitHub üzerinden en son sürüm bilgisi alınıyor.",
            fill=c['muted'], font=("Segoe UI", 9), justify=tk.LEFT))

        bx, by = LAYOUT_R['bar']
        self.progress = _ImageProgress(
            canvas, (bx, by + T), img['bar.png'], img['bar_fill.png'],
            img['bar_fill_busy.png'], LAYOUT_R['bar_inner'])

        # --- butonlar ---
        def states(key):
            return {s: img[f'btn_{key}_{s}.png']
                    for s in ('normal', 'hover', 'pressed', 'disabled')}

        def box(key):
            x, y, w, h = LAYOUT_R[key]
            return (x, y + T, w, h)

        btn_font = ("Georgia", 13, "bold")
        self.play_btn = _ImageButton(canvas, states('play'), box('btn_play'),
                                     "OYNA", self._launch_game, btn_font)
        self.update_btn = _ImageButton(canvas, states('update'), box('btn_update'),
                                       "GÜNCELLE", self._start_update, btn_font)
        self.notes_btn = _ImageButton(canvas, states('notes'), box('btn_notes'),
                                      "YENİLİKLER (PATCH NOTES)",
                                      self._show_patch_notes, btn_font)

        canvas.create_text(
            W // 2, H - 26, text=(
                "Güncellemeler doğrulanarak uygulanır  •  Kayıt dosyaların korunur"),
            fill='#6c7a8c', font=("Segoe UI", 9))

        self.root.bind('<Escape>', lambda _e: self._quit())

    # --- ozel baslik cubugu davranisi ---
    def _drag_start(self, event):
        self._drag_from = (event.x_root - self.root.winfo_x(),
                           event.y_root - self.root.winfo_y())

    def _drag_move(self, event):
        if not getattr(self, '_drag_from', None):
            return
        dx, dy = self._drag_from
        self.root.geometry(f"+{event.x_root - dx}+{event.y_root - dy}")

    def _minimize(self):
        """overrideredirect pencere dogrudan iconify edilemez; gecici olarak
        cerceveyi geri acip kucultur, geri gelince tekrar kaldirir."""
        try:
            self.root.overrideredirect(False)
            self.root.iconify()

            def restore(_e=None):
                self.root.overrideredirect(True)
                self.root.unbind('<Map>', self._map_bind)
                self._map_bind = None

            self._map_bind = self.root.bind('<Map>', restore)
        except Exception as error:
            print(f"[launcher] kucultme desteklenmiyor: {error}")

    def _quit(self):
        self.root.destroy()

    def _build_ui_classic(self):
        # Koyu fantastik tema paleti (oyunla ortak; bkz. DESIGN.md / ui_theme.COLORS)
        self.colors = {
            'window': '#181416', 'panel': '#1a1822', 'panel_alt': '#141218',
            'border': '#7a7e86', 'text': '#f0eadc', 'muted': '#8c8470',
            'gold': '#966416', 'blue': '#1e4e6e', 'green': '#2c603a',
            'orange': '#b47a1e', 'red': '#92180f',
        }
        self.root.option_add('*Font', '{Segoe UI} 10')

        shell = tk.Frame(self.root, bg=self.colors['window'])
        shell.pack(fill=tk.BOTH, expand=True, padx=34, pady=26)

        brand = tk.Frame(shell, bg=self.colors['window'])
        brand.pack(fill=tk.X)
        accent = tk.Frame(brand, bg=self.colors['gold'], width=5, height=86)
        accent.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))
        accent.pack_propagate(False)

        brand_copy = tk.Frame(brand, bg=self.colors['window'])
        brand_copy.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(
            brand_copy, text="NATIVE EVOLUTION", font=("Segoe UI", 9, "bold"),
            fg=self.colors['blue'], bg=self.colors['window'], anchor='w',
        ).pack(fill=tk.X)
        tk.Label(
            brand_copy, text="BOXHEAD 2.0", font=("Segoe UI", 30, "bold"),
            fg=self.colors['text'], bg=self.colors['window'], anchor='w',
        ).pack(fill=tk.X, pady=(1, 0))
        tk.Label(
            brand_copy, text="Hayatta kal. Güçlen. Sınırları aş.",
            font=("Segoe UI", 10), fg=self.colors['muted'],
            bg=self.colors['window'], anchor='w',
        ).pack(fill=tk.X)

        version_box = tk.Frame(brand, bg=self.colors['panel_alt'], padx=14, pady=10)
        version_box.pack(side=tk.RIGHT, anchor='n', pady=4)
        self.version_label = tk.Label(
            version_box,
            text=f"OYUN  v{get_local_version()}\nLAUNCHER  v{LAUNCHER_VERSION}",
            font=("Consolas", 9, "bold"), fg=self.colors['muted'],
            bg=self.colors['panel_alt'], justify=tk.LEFT,
        )
        self.version_label.pack()

        status_card = tk.Frame(
            shell, bg=self.colors['panel'], highlightbackground=self.colors['border'],
            highlightthickness=1, padx=22, pady=18,
        )
        status_card.pack(fill=tk.X, pady=(24, 18))

        status_head = tk.Frame(status_card, bg=self.colors['panel'])
        status_head.pack(fill=tk.X)
        self.status_dot = tk.Label(
            status_head, text="●", font=("Segoe UI", 13),
            fg=self.colors['blue'], bg=self.colors['panel'],
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 9))
        self.status_label = tk.Label(
            status_head, text="Sürüm kontrol ediliyor",
            font=("Segoe UI", 13, "bold"), fg=self.colors['text'],
            bg=self.colors['panel'], anchor='w',
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_detail = tk.Label(
            status_card, text="GitHub üzerinden en son sürüm bilgisi alınıyor.",
            font=("Segoe UI", 9), fg=self.colors['muted'], bg=self.colors['panel'],
            anchor='w', justify=tk.LEFT, wraplength=620,
        )
        self.status_detail.pack(fill=tk.X, pady=(7, 13))

        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Boxhead.Horizontal.TProgressbar",
            troughcolor=self.colors['panel_alt'], background=self.colors['blue'],
            bordercolor=self.colors['panel_alt'], lightcolor=self.colors['blue'],
            darkcolor=self.colors['blue'], thickness=8,
        )
        self.progress = ttk.Progressbar(
            status_card, mode='determinate', maximum=100,
            style="Boxhead.Horizontal.TProgressbar",
        )
        self.progress.pack(fill=tk.X)

        actions = tk.Frame(shell, bg=self.colors['window'])
        actions.pack(fill=tk.X)
        actions.grid_columnconfigure(0, weight=1, uniform='actions')
        actions.grid_columnconfigure(1, weight=1, uniform='actions')
        self.play_btn = self._make_button(
            actions, "OYNA", self.colors['red'], '#b8281c', self._launch_game,
        )
        self.play_btn.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        self.update_btn = self._make_button(
            actions, "GÜNCELLE", self.colors['gold'], '#b47a1e', self._start_update,
        )
        self.update_btn.grid(row=0, column=1, sticky='ew', padx=(8, 0))
        self.notes_btn = self._make_button(
            actions, "YENİLİKLER (PATCH NOTES)", self.colors['blue'], '#266089',
            self._show_patch_notes,
        )
        self.notes_btn.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10, 0))

        footer = tk.Label(
            shell,
            text="Güncellemeler doğrulanarak uygulanır  •  Kayıt dosyaların korunur",
            font=("Segoe UI", 9), fg='#667386', bg=self.colors['window'],
        )
        footer.pack(pady=(18, 0))

    def _make_button(self, parent, text, bg, hover_bg, command):
        button = tk.Button(
            parent, text=text, font=("Georgia", 12, "bold"), fg='#f0eadc', bg=bg,
            activeforeground='white', activebackground=hover_bg,
            disabledforeground='#687386', relief=tk.FLAT, bd=0, height=2,
            cursor='hand2', command=command,
        )
        button._normal_bg = bg
        button._hover_bg = hover_bg
        button.bind('<Enter>', lambda _e, b=button: self._hover_button(b, True))
        button.bind('<Leave>', lambda _e, b=button: self._hover_button(b, False))
        return button

    @staticmethod
    def _hover_button(button, hovered):
        if button.cget('state') == tk.NORMAL:
            button.configure(bg=button._hover_bg if hovered else button._normal_bg)

    def _set_status(self, text: str, color=None, detail=None):
        """Thread-safe status update."""
        def apply():
            self.status_label.configure(text=text)
            if color:
                self.status_dot.configure(fg=color)
            if detail is not None:
                self.status_detail.configure(text=detail)
        self.root.after(0, apply)

    def _stop_progress(self, value=0):
        self.progress.stop()
        self.progress.configure(mode='determinate', value=value)

    def _check_updates(self):
        self._check_generation = getattr(self, '_check_generation', 0) + 1
        generation = self._check_generation
        self.release_info = None
        self.update_btn.configure(text="KONTROL EDİLİYOR", state=tk.DISABLED)
        self.play_btn.configure(
            text="OYNA", state=tk.NORMAL if self._game_exists() else tk.DISABLED
        )
        self.progress.configure(mode='indeterminate', value=0)
        self.progress.start(12)
        self._set_status(
            "Sürüm kontrol ediliyor", self.colors['blue'],
            "Kontrol arka planda sürer; oyun kuruluysa beklemeden oynayabilirsin.",
        )
        self.root.after(6500, lambda gen=generation: self._expire_update_check(gen))

        def worker():
            try:
                release_info = fetch_latest_release()
                if generation != self._check_generation:
                    return
                self.release_info = release_info
                remote_ver = release_info['version']
                local_ver = get_local_version()
                min_lv = release_info.get('min_launcher_version', '1.0.0')

                if compare_versions(LAUNCHER_VERSION, min_lv) < 0:
                    self._set_status(
                        "Launcher güncellemesi gerekli", self.colors['red'],
                        f"Bu sürüm Launcher v{min_lv} veya üzerini gerektiriyor.",
                    )
                    self.root.after(0, self._disable_actions)
                elif compare_versions(remote_ver, local_ver) > 0:
                    self.root.after(0, self._show_update_available)
                else:
                    self.root.after(0, self._show_ready)
            except Exception as error:
                if generation != self._check_generation:
                    return
                self._set_status(
                    "Sunucuya ulaşılamadı", self.colors['orange'],
                    f"Kontrol kısa sürede durduruldu. {error}",
                )
                self.root.after(0, self._show_offline_state)

        threading.Thread(target=worker, daemon=True).start()

    def _expire_update_check(self, generation):
        if generation != self._check_generation or self.release_info is not None:
            return
        # Nesli bozma: yavaş ağlarda geç gelen sonuç yine de UI'a yansısın.
        # Şimdilik çevrimdışı durumu göster ki kullanıcı beklemeden oynayabilsin.
        self._set_status(
            "Kontrol uzun sürüyor", self.colors['orange'],
            "Yanıt gecikti; kontrol arka planda sürüyor. Çevrimdışı oynayabilirsin.",
        )
        self._show_offline_state()

    def _start_update(self):
        if not self.release_info:
            self._check_updates()
            return
        if is_game_running():
            messagebox.showwarning(
                "Oyun Çalışıyor", "Güncellemeden önce Boxhead'i kapatmalısın."
            )
            return

        self.update_btn.configure(text="GÜNCELLENİYOR", state=tk.DISABLED)
        self.play_btn.configure(state=tk.DISABLED)
        self._stop_progress(0)

        def worker():
            success = False
            try:
                info = self.release_info
                zip_path = os.path.join(
                    self.install_dir, f"Boxhead-{info['version']}-win64.zip"
                )
                self._set_status(
                    "Güncelleme indiriliyor", self.colors['blue'], "Paket hazırlanıyor..."
                )

                def on_progress(downloaded, total):
                    if total > 0:
                        pct = min(100, int(downloaded / total * 100))
                        self.root.after(0, lambda p=pct: self.progress.configure(value=p))
                        self._set_status(
                            "Güncelleme indiriliyor", self.colors['blue'],
                            f"İndirme ilerlemesi: %{pct}",
                        )

                download_file(info['download_url'], zip_path, on_progress)

                if info.get('size') and os.path.getsize(zip_path) != info['size']:
                    raise RuntimeError('İndirilen dosyanın boyutu beklenen değerle uyuşmuyor.')

                if info.get('sha256'):
                    self._set_status(
                        "Paket doğrulanıyor", self.colors['gold'],
                        "SHA-256 bütünlük kontrolü yapılıyor.",
                    )
                    actual = sha256_file(zip_path)
                    if actual != info['sha256']:
                        os.remove(zip_path)
                        raise RuntimeError('Paket doğrulaması başarısız oldu; dosya silindi.')

                self._set_status(
                    "Güncelleme uygulanıyor", self.colors['gold'],
                    "Kayıt dosyaların korunarak oyun dosyaları yenileniyor.",
                )
                perform_update(zip_path, self.install_dir)
                self._set_status(
                    "Güncelleme tamamlandı", self.colors['green'],
                    "Yeni sürüm hazır. Oyuna başlayabilirsin.",
                )
                self.root.after(0, lambda: self.progress.configure(value=100))
                self.root.after(
                    0,
                    lambda: self.version_label.configure(
                        text=f"OYUN  v{info['version']}\nLAUNCHER  v{LAUNCHER_VERSION}"
                    ),
                )
                success = True
            except Exception as error:
                self._set_status(
                    "Güncelleme tamamlanamadı", self.colors['red'], str(error)
                )
                self.root.after(
                    0,
                    lambda message=str(error): messagebox.showerror(
                        "Güncelleme Hatası", message
                    ),
                )
            finally:
                self.root.after(0, lambda ok=success: self._finish_update(ok))

        threading.Thread(target=worker, daemon=True).start()

    def _game_exists(self):
        return os.path.exists(os.path.join(self.install_dir, 'Boxhead.exe'))

    def _disable_actions(self):
        self._stop_progress(0)
        self.update_btn.configure(text="LAUNCHER GEREKLİ", state=tk.DISABLED)
        self.play_btn.configure(state=tk.DISABLED)

    def _show_update_available(self):
        self._stop_progress(0)
        remote = self.release_info['version']
        local = get_local_version()
        size = self.release_info.get('size', 0)
        size_text = f" • {size / (1024 * 1024):.1f} MB" if size else ""
        self._set_status(
            f"Yeni sürüm hazır: v{remote}", self.colors['orange'],
            f"Kurulu sürüm v{local}{size_text}. Güncelleme önerilir.",
        )
        self.update_btn.configure(
            text="ŞİMDİ GÜNCELLE", command=self._start_update, state=tk.NORMAL
        )
        self.play_btn.configure(
            text="ŞİMDİLİK OYNA" if self._game_exists() else "OYNA",
            state=tk.NORMAL if self._game_exists() else tk.DISABLED,
        )

    def _show_ready(self):
        self._stop_progress(100)
        if self._game_exists():
            self._set_status(
                "Oyun güncel", self.colors['green'],
                "En son sürüm kurulu. Savaşa hazırsın.",
            )
            self.update_btn.configure(text="GÜNCEL", state=tk.DISABLED)
            self.play_btn.configure(text="OYNA", state=tk.NORMAL)
        else:
            self.update_btn.configure(
                text="OYUNU KUR", command=self._start_update, state=tk.NORMAL
            )
            self.play_btn.configure(state=tk.DISABLED)
            self._set_status(
                "Oyun kuruluma hazır", self.colors['blue'],
                "Dosyaları indirmek için Oyunu Kur'a bas.",
            )

    def _show_offline_state(self):
        self._stop_progress(0)
        self.update_btn.configure(
            text="TEKRAR DENE", command=self._check_updates, state=tk.NORMAL
        )
        self.play_btn.configure(
            text="ÇEVRİMDIŞI OYNA",
            state=tk.NORMAL if self._game_exists() else tk.DISABLED,
        )

    def _finish_update(self, success):
        if success:
            self.update_btn.configure(text="GÜNCEL", state=tk.DISABLED)
            self.play_btn.configure(text="OYNA", state=tk.NORMAL)
        else:
            self.update_btn.configure(
                text="TEKRAR DENE", command=self._start_update,
                state=tk.NORMAL if self.release_info else tk.DISABLED,
            )
            self.play_btn.configure(
                text="OYNA", state=tk.NORMAL if self._game_exists() else tk.DISABLED,
            )

    def _show_patch_notes(self):
        notes_path = os.path.join(self.install_dir, 'data', 'patch_notes.json')
        try:
            import json
            with open(notes_path, 'r', encoding='utf-8') as f:
                versions = json.load(f).get('versions', [])
        except (OSError, ValueError):
            messagebox.showinfo(
                "Yenilikler",
                "Patch notes dosyası bulunamadı. Oyunu güncelledikten sonra tekrar dene.",
            )
            return

        win = tk.Toplevel(self.root)
        win.title("Boxhead 2.0 — Yenilikler")
        win.geometry("620x540")
        win.configure(bg=self.colors['window'])
        win.transient(self.root)

        tk.Label(
            win, text="YENİLİKLER", font=("Segoe UI", 16, "bold"),
            fg=self.colors['gold'], bg=self.colors['window'],
        ).pack(pady=(16, 8))

        frame = tk.Frame(win, bg=self.colors['panel'])
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text = tk.Text(
            frame, wrap=tk.WORD, bg=self.colors['panel'], fg=self.colors['text'],
            relief=tk.FLAT, padx=16, pady=12, yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10), cursor='arrow',
        )
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.configure(command=text.yview)

        text.tag_configure('version', font=("Segoe UI", 13, "bold"), foreground=self.colors['gold'], spacing1=10)
        text.tag_configure('category', font=("Segoe UI", 10, "bold"), foreground=self.colors['blue'], spacing1=6)
        text.tag_configure('note', foreground=self.colors['text'], lmargin1=18, lmargin2=30)
        text.tag_configure('sep', foreground=self.colors['border'])

        if not versions:
            text.insert(tk.END, "Henüz patch notu yok.\n", 'note')
        for entry in versions:
            text.insert(tk.END, f"v{entry['version']}  •  {entry.get('date', '')}\n", 'version')
            for cat, items in entry.get('categories', {}).items():
                text.insert(tk.END, f"{cat}\n", 'category')
                for note in items:
                    text.insert(tk.END, f"• {note}\n", 'note')
            text.insert(tk.END, "─" * 60 + "\n", 'sep')
        text.configure(state=tk.DISABLED)

    def _launch_game(self):
        try:
            launch_game(self.install_dir)
            self.root.after(1000, self.root.destroy)
        except Exception as error:
            messagebox.showerror("Başlatma Hatası", str(error))

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    LauncherApp().run()
