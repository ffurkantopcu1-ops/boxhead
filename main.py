import pygame
import sys
import os

# PyInstaller EXE içinden veya Launcher'dan çalışırken path desteği
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.getcwd())

from scene_manager import SceneManager, load_global_settings, create_display

def main():
    pygame.init()

    # Mantıksal çözünürlük her modda masaüstü çözünürlüğüdür (sahne yerleşimi sabit)
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h

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
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        scene_manager.update(dt, events)
        scene_manager.draw()
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
