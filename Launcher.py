import pygame
import requests
import zipfile
import subprocess
import os
import json
import shutil
import threading
import time
import sys

# --- YAPILANDIRMA (CONFIG) ---
GITHUB_USER = "ffurkantopcu1-ops"
REPO_NAME = "boxhead-updates"
MANIFEST_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/version.json"
# Not: Release indirme linki versiyon.json içinden gelecek, ancak yedek olarak:
FALLBACK_ZIP_URL = f"https://github.com/{GITHUB_USER}/{REPO_NAME}/releases/latest/download/Boxhead2.0.zip"

VERSION_FILE = "version.txt"
GAME_ENTRY = "main.py"
SAVES_DIR = "saves"

class Launcher:
    def __init__(self):
        pygame.init()
        self.width, self.height = 900, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Boxhead 2.0 Launcher & Updater")
        
        self.font_main = pygame.font.SysFont("Segoe UI, Arial", 32, bold=True)
        self.font_sub = pygame.font.SysFont("Segoe UI, Arial", 18)
        self.font_notes = pygame.font.SysFont("Consolas, Courier", 16)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # States
        self.status = "Kontrol ediliyor..."
        self.progress = 0
        self.local_version = self.get_local_version()
        self.remote_version = None
        self.update_available = False
        self.is_updating = False
        self.patch_notes = []
        self.download_url = ""
        self.scroll_y = 0
        self.max_scroll = 0
        
        # UI Elements
        self.play_btn_rect = pygame.Rect(self.width // 2 - 150, self.height - 100, 300, 60)
        self.check_updates()

    def get_local_version(self):
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                return f.read().strip()
        return "0.0.0"

    def check_updates(self):
        def _check():
            try:
                # Cache Busting: Linke zaman damgası ekleyerek her zaman taze veri al
                url = f"{MANIFEST_URL}?t={int(time.time())}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.remote_version = data.get("version", "1.0.0")
                    self.patch_notes = data.get("changes", []) # 'notes' yerine 'changes' kullanıldı
                    self.download_url = data.get("url", FALLBACK_ZIP_URL)
                    
                    if self.remote_version > self.local_version:
                        self.update_available = True
                        self.status = f"Yeni Sürüm Mevcut: v{self.remote_version}"
                    else:
                        self.status = "Oyun Güncel"
                else:
                    self.status = "Sunucuya bağlanılamadı."
            except Exception as e:
                self.status = f"Bağlantı Hatası: {str(e)}"
        
        threading.Thread(target=_check).start()

    def start_update(self):
        if self.is_updating: return
        self.is_updating = True
        self.status = "Güncelleme indiriliyor..."
        
        # 0. Ön Temizlik: Eğer oyun açıksa kapat (Permission Denied hatasını engeller)
        if os.name == 'nt': # Windows
            try:
                # Hem EXE hem de olası Python süreçlerini temizlemeye çalış
                subprocess.run(["taskkill", "/F", "/IM", "Boxhead.exe", "/T"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq Boxhead*", "/T"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2) # Dosya kilitlerinin tamamen kalkması için biraz daha uzun bekle
            except: pass
        
        def _update_task():
            try:
                # 1. Dosyayı İndir
                response = requests.get(self.download_url, stream=True)
                
                # Hata Kontrolü: Eğer URL yanlışsa (404 vb.) indirmeyi durdur
                if response.status_code != 200:
                    self.status = f"Hata: İndirme başarısız ({response.status_code})"
                    self.is_updating = False
                    return

                total_size = int(response.headers.get('content-length', 0))
                
                downloaded = 0
                temp_zip = "update.zip"
                with open(temp_zip, "wb") as f:
                    for chunk in response.iter_content(chunk_size=4096):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                self.progress = (downloaded / total_size) * 100
                
                # 2. Arşivi Aç (Sırayla)
                self.status = "Dosyalar kuruluyor..."
                my_name = os.path.basename(sys.executable)
                with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                    # saves/ dışındaki her şeyi çıkart, ama kendini ve versiyon dosyasını atla
                    for file in zip_ref.namelist():
                        if file.startswith(SAVES_DIR) or file == my_name or file == VERSION_FILE or file == "Launcher.py":
                            continue
                        # Kilitli dosyalar için 3 kez deneme yap
                        success = False
                        for _ in range(3):
                            try:
                                zip_ref.extract(file, ".")
                                success = True
                                break
                            except PermissionError:
                                time.sleep(1) # 1 saniye bekle ve tekrar dene
                        
                        if not success:
                            self.status = f"Hata: {file} kilitli! Lütfen oyunu kapatıp tekrar deneyin."
                            self.is_updating = False
                            return
                
                # 3. Temizlik
                if os.path.exists(temp_zip):
                    os.remove(temp_zip)
                
                # 4. Versiyonu Güncelle
                with open(VERSION_FILE, "w") as f:
                    f.write(self.remote_version)
                
                self.local_version = self.remote_version
                self.update_available = False
                self.is_updating = False
                self.status = "Güncelleme Tamamlandı!"
                self.progress = 100
            except Exception as e:
                self.status = f"Hata: {str(e)}"
                self.is_updating = False
        
        threading.Thread(target=_update_task).start()

    def launch_game(self):
        try:
            # 1. Eğer klasörde derlenmiş oyun varsa (Boxhead.exe), onu çalıştır (ARKADAŞLARIN İÇİN)
            if os.path.exists("Boxhead.exe"):
                # Windows'ta ./ kullanımı bazen daha güvenlidir
                subprocess.Popen([os.path.abspath("Boxhead.exe")])
            
            # 2. Eğer EXE yoksa ama main.py varsa, SİSTEMDEKİ Python ile çalıştır (SENİN İÇİN)
            elif os.path.exists("main.py"):
                # sys.executable eğer bir EXE (Launcher) ise, script çalıştıramaz. 
                # O yüzden "python" komutunu deniyoruz.
                try:
                    subprocess.Popen(["python", "main.py"])
                except:
                    # Alternatif: python3
                    subprocess.Popen(["python3", "main.py"])
            
            # Başlattıktan sonra Launcher'ı kapat
            self.running = False
        except Exception as e:
            self.status = f"Başlatma Hatası: {str(e)}"

    def wrap_text(self, text, font, max_width):
        """Metni belirtilen genişliğe göre satırlara böler."""
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] < max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def draw(self):
        self.screen.fill((20, 20, 30)) # Koyu Premium Arka Plan
        
        # Grafiksel Başlık
        title = self.font_main.render("BOXHEAD 2.0", True, (241, 196, 15))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 40))
        
        # Versiyon ve Durum
        v_info = f"Mevcut Sürüm: v{self.local_version} | Status: {self.status}"
        v_surf = self.font_sub.render(v_info, True, (150, 150, 150))
        self.screen.blit(v_surf, (self.width // 2 - v_surf.get_width() // 2, 90))
        
        notes_rect = pygame.Rect(100, 140, 700, 300)
        pygame.draw.rect(self.screen, (35, 35, 50), notes_rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 120), notes_rect, width=2, border_radius=10)
        
        notes_title = self.font_sub.render("YENİLİKLER VE GÜNCELLEME NOTLARI", True, (52, 152, 219))
        self.screen.blit(notes_title, (120, 155))
        
        # Notları Çiz (Clipped & Scrolled)
        draw_area = notes_rect.inflate(-40, -100)
        draw_area.y += 40 # Başlığın altına kaydır
        self.screen.set_clip(draw_area)
        
        y_off = draw_area.y + self.scroll_y
        if not self.patch_notes:
            msg = self.font_notes.render("Güncelleme notları yükleniyor...", True, (100, 100, 100))
            self.screen.blit(msg, (120, y_off))
        else:
            total_h = 0
            for note in self.patch_notes:
                wrapped = self.wrap_text(f"• {note}", self.font_notes, draw_area.width)
                for line in wrapped:
                    n_surf = self.font_notes.render(line, True, (200, 200, 200))
                    self.screen.blit(n_surf, (120, y_off))
                    y_off += 25
                    total_h += 25
            self.max_scroll = max(0, total_h - draw_area.height)
            
        self.screen.set_clip(None)

        # Progress Bar (Sadece güncelleme varsa veya iniyorsa)
        if self.is_updating or (self.progress > 0 and self.progress < 100):
            bar_rect = pygame.Rect(100, 460, 700, 15)
            pygame.draw.rect(self.screen, (45, 45, 60), bar_rect, border_radius=8)
            pygame.draw.rect(self.screen, (46, 204, 113), (100, 460, 700 * (self.progress / 100), 15), border_radius=8)

        # Buton Çizimi
        m_pos = pygame.mouse.get_pos()
        btn_hover = self.play_btn_rect.collidepoint(m_pos)
        
        if self.update_available:
            btn_text = "GÜNCELLE"
            btn_color = (230, 126, 34) if btn_hover else (211, 84, 0)
        elif self.is_updating:
            btn_text = "İNDİRİLİYOR..."
            btn_color = (127, 140, 141)
        else:
            btn_text = "OYNA"
            btn_color = (46, 204, 113) if btn_hover else (39, 174, 96)
            
        pygame.draw.rect(self.screen, btn_color, self.play_btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), self.play_btn_rect, width=2, border_radius=12)
        
        t_surf = self.font_main.render(btn_text, True, (255, 255, 255))
        self.screen.blit(t_surf, t_surf.get_rect(center=self.play_btn_rect.center))

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.play_btn_rect.collidepoint(event.pos):
                        if self.update_available:
                            self.start_update()
                        elif not self.is_updating:
                            self.launch_game()
                if event.type == pygame.MOUSEWHEEL:
                    self.scroll_y += event.y * 30
                    self.scroll_y = max(-self.max_scroll, min(0, self.scroll_y))
            
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()

if __name__ == "__main__":
    launcher = Launcher()
    launcher.run()
