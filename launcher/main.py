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

    def _build_ui(self):
        self.colors = {
            'window': '#0d1018', 'panel': '#171c29', 'panel_alt': '#111622',
            'border': '#2c3850', 'text': '#f3f5f8', 'muted': '#8e9aab',
            'gold': '#f1c40f', 'blue': '#3498db', 'green': '#2ecc71',
            'orange': '#e67e22', 'red': '#e74c3c',
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
            actions, "OYNA", self.colors['green'], '#27ae60', self._launch_game,
        )
        self.play_btn.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        self.update_btn = self._make_button(
            actions, "GÜNCELLE", self.colors['orange'], '#d35400', self._start_update,
        )
        self.update_btn.grid(row=0, column=1, sticky='ew', padx=(8, 0))
        self.notes_btn = self._make_button(
            actions, "YENİLİKLER (PATCH NOTES)", self.colors['blue'], '#2980b9',
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
            parent, text=text, font=("Segoe UI", 12, "bold"), fg='white', bg=bg,
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
