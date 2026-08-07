import pygame
import sys
import os

# PyInstaller EXE içinden veya Launcher'dan çalışırken path desteği
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.getcwd())

from scene_manager import SceneManager

def main():
    pygame.init()
    
    # Borderless Fullscreen ayarı
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h
    
    # Gerçek Borderless için NOFRAME ve FULLSCREEN kombinasyonu
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME | pygame.FULLSCREEN)
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
