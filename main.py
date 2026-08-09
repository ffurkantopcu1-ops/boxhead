import pygame
import sys
import os

# Konsol çıktısını UTF-8'e sabitle. Türkçe Windows'ta varsayılan kod sayfası
# cp1252/cp857 olduğu için "EVRİM", "kazanıldı" gibi metinler içeren print()
# çağrıları UnicodeEncodeError atıp oyunu kaynak koddan çalıştırırken çökertiyordu.
# (Paketlenmiş exe'de console=False olduğu için stdout None'dır ve etkilenmez.)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass  # stdout None (windowed exe) veya reconfigure desteklenmiyor

# PyInstaller EXE içinden veya Launcher'dan çalışırken path desteği
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.getcwd())

from scene_manager import SceneManager, load_global_settings, create_display

def main():
    pygame.init()

    # Oyunun UI'ı 1920x1080 çözünürlüğüne göre tasarlandığı için mantıksal çözünürlüğü sabitliyoruz.
    # pygame.SCALED bu 1920x1080 yüzeyi her ekrana bozulmadan (siyah barlarla) sığdırır.
    screen_width = 1920
    screen_height = 1080

    # Kayıtlı ekran moduna göre pencere: fullscreen / borderless / windowed
    settings = load_global_settings()
    screen = create_display(settings.get("display_mode", "fullscreen"), screen_width, screen_height)
    pygame.display.set_caption("Boxhead 2.0: Native Evolution")
    
    clock = pygame.time.Clock()
    scene_manager = SceneManager(screen, screen_width, screen_height)
    
    running = True
    while running:
        dt = clock.tick(144) / 1000.0 # 144 FPS hedefi, dt saniye cinsinden
        
        events = pygame.event.get()
        
        # Fare koordinatlarını fiziksel pencereden mantıksal çözünürlüğe ölçekle
        scale_x = screen_width / scene_manager.real_screen.get_width()
        scale_y = screen_height / scene_manager.real_screen.get_height()
        
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                event.pos = (int(event.pos[0] * scale_x), int(event.pos[1] * scale_y))
        
        # Sahneler içinde anlık fare pozisyonu okuyan (pygame.mouse.get_pos) fonksiyonu geçici olarak yamala
        old_get_pos = pygame.mouse.get_pos
        pygame.mouse.get_pos = lambda: (int(old_get_pos()[0] * scale_x), int(old_get_pos()[1] * scale_y))
        
        scene_manager.update(dt, events)
        # draw() içindeki hover mantığı da (InventorySlot.update, Button.draw)
        # pygame.mouse.get_pos okuyor; yama çizimi de kapsamalı, yoksa tam
        # ekranda hover imlecin olduğu yerde değil ölçeksiz konumda çıkıyordu.
        scene_manager.draw()

        # Orijinal fonksiyona geri dön
        pygame.mouse.get_pos = old_get_pos

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
