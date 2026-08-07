"""Boxhead Launcher - Tkinter GUI with secure auto-update."""
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
        self.root.title("Boxhead 2.0 Launcher")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        self.root.configure(bg='#14141e')

        self.release_info = None

        self._build_ui()
        self.root.after(100, self._check_updates)

    def _build_ui(self):
        # Title
        title = tk.Label(
            self.root, text="BOXHEAD 2.0",
            font=("Segoe UI", 24, "bold"),
            fg="#f1c40f", bg="#14141e",
        )
        title.pack(pady=(20, 5))

        # Version info
        local = get_local_version()
        self.version_label = tk.Label(
            self.root,
            text=f"Mevcut: v{local} | Launcher: v{LAUNCHER_VERSION}",
            font=("Segoe UI", 10), fg="#969696", bg="#14141e",
        )
        self.version_label.pack()

        # Status
        self.status_label = tk.Label(
            self.root, text="Güncelleme kontrol ediliyor...",
            font=("Segoe UI", 11), fg="#bdc3c7", bg="#14141e",
        )
        self.status_label.pack(pady=(30, 10))

        # Progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "green.Horizontal.TProgressbar",
            troughcolor='#2d2d3c', background='#2ecc71', thickness=20,
        )
        self.progress = ttk.Progressbar(
            self.root, length=400, mode='determinate',
            style="green.Horizontal.TProgressbar",
        )
        self.progress.pack(pady=10)

        # Buttons
        btn_frame = tk.Frame(self.root, bg='#14141e')
        btn_frame.pack(pady=20)

        self.update_btn = tk.Button(
            btn_frame, text="GÜNCELLE",
            font=("Segoe UI", 12, "bold"),
            fg="white", bg="#e67e22", activebackground="#d35400",
            width=15, height=2, command=self._start_update,
            state=tk.DISABLED,
        )
        self.update_btn.pack(side=tk.LEFT, padx=10)

        self.play_btn = tk.Button(
            btn_frame, text="OYNA",
            font=("Segoe UI", 12, "bold"),
            fg="white", bg="#27ae60", activebackground="#1e8449",
            width=15, height=2, command=self._launch_game,
        )
        self.play_btn.pack(side=tk.LEFT, padx=10)

    def _set_status(self, text: str):
        """Thread-safe status update."""
        self.root.after(0, lambda: self.status_label.configure(text=text))

    def _check_updates(self):
        def _worker():
            try:
                self.release_info = fetch_latest_release()
                remote_ver = self.release_info['version']
                local_ver = get_local_version()

                # Launcher compatibility check
                min_lv = self.release_info.get('min_launcher_version', '1.0.0')
                if compare_versions(LAUNCHER_VERSION, min_lv) < 0:
                    self._set_status(
                        f"Launcher güncellenmeli! (min: v{min_lv})"
                    )
                    return

                if compare_versions(remote_ver, local_ver) > 0:
                    self._set_status(f"Yeni sürüm mevcut: v{remote_ver}")
                    self.root.after(
                        0,
                        lambda: self.update_btn.configure(state=tk.NORMAL),
                    )
                else:
                    self._set_status("Oyun güncel ✓")
            except Exception as e:
                self._set_status(f"Bağlantı hatası: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _start_update(self):
        if is_game_running():
            messagebox.showwarning(
                "Uyarı", "Oyun çalışıyor! Lütfen önce oyunu kapatın."
            )
            return

        self.update_btn.configure(state=tk.DISABLED)
        self.play_btn.configure(state=tk.DISABLED)

        def _worker():
            try:
                info = self.release_info
                zip_path = os.path.join(
                    self.install_dir,
                    f"Boxhead-{info['version']}-win64.zip",
                )

                # Download with progress
                self._set_status("İndiriliyor...")

                def on_progress(downloaded, total):
                    if total > 0:
                        pct = int(downloaded / total * 100)
                        self.root.after(
                            0,
                            lambda p=pct: self.progress.configure(value=p),
                        )

                download_file(info['download_url'], zip_path, on_progress)

                # Verify file size
                if info.get('size') and os.path.getsize(zip_path) != info['size']:
                    raise RuntimeError('İndirilen dosya boyutu beklenenden farklı')

                # Verify SHA-256 checksum
                if info.get('sha256'):
                    self._set_status("Doğrulanıyor...")
                    actual = sha256_file(zip_path)
                    if actual != info['sha256']:
                        os.remove(zip_path)
                        raise RuntimeError(
                            f'Checksum uyuşmazlığı!\n'
                            f'Beklenen: {info["sha256"]}\n'
                            f'Gerçek: {actual}'
                        )

                # Apply update
                self._set_status("Güncelleme uygulanıyor...")
                perform_update(zip_path, self.install_dir)

                self._set_status("Güncelleme tamamlandı! ✓")
                self.root.after(
                    0, lambda: self.progress.configure(value=100)
                )
                self.root.after(
                    0,
                    lambda: self.version_label.configure(
                        text=(
                            f"Mevcut: v{info['version']}"
                            f" | Launcher: v{LAUNCHER_VERSION}"
                        )
                    ),
                )

            except Exception as e:
                self._set_status(f"Hata: {e}")
                messagebox.showerror("Güncelleme Hatası", str(e))
            finally:
                self.root.after(
                    0, lambda: self.play_btn.configure(state=tk.NORMAL)
                )

        threading.Thread(target=_worker, daemon=True).start()

    def _launch_game(self):
        try:
            launch_game(self.install_dir)
            self.root.after(1000, self.root.destroy)
        except Exception as e:
            messagebox.showerror("Başlatma Hatası", str(e))

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    app = LauncherApp()
    app.run()
