import pygame
import math
import random
from entities.enemy import Enemy
from entities.projectile import Projectile

class Arachne(Enemy):
    def __init__(self, id, x, y, game, wave_level=30):
        super().__init__(id, x, y, game, type="arachne", wave_level=wave_level)
        self.max_hp = 100000 * (1.25 ** (wave_level // 10))
        self.hp = self.max_hp
        self.speed = 3.0
        self.radius = 70
        self.dmg = 200
        self.color = (138, 43, 226) # Mor (Spider Queen)
        self.xp_reward = 8000
        self.is_boss = True

        self.egg_timer = 5.0
        self.web_timer = 4.0
        self.base_speed = self.speed
        
    def update(self, dt, game):
        super().update(dt, game)
        if self.dead: return
            
        self.egg_timer -= dt
        if self.egg_timer <= 0:
            self.spawn_eggs(game)
            self.egg_timer = 6.0
            
        self.web_timer -= dt
        if self.web_timer <= 0:
            self.shoot_web(game)
            self.web_timer = 4.0
            
    def spawn_eggs(self, game):
        game.add_event("damage_text", self.x, self.y - 80, value="YUMURTALAR!", color=(138, 43, 226), timer=1.5)
        # 3 adet örümcek yavrusu (spiderling) yumurtla
        for i in range(3):
            spawn_x = self.x + random.randint(-80, 80)
            spawn_y = self.y + random.randint(-80, 80)
            # Normal Enemy objesi yaratalım, türü spiderling olsun
            spiderling = Enemy(game.entity_id_counter, spawn_x, spawn_y, game, type="spiderling", wave_level=game.wave.get("level", 30))
            spiderling.max_hp = self.max_hp * 0.05
            spiderling.hp = spiderling.max_hp
            spiderling.speed = 5.0
            spiderling.radius = 15
            spiderling.dmg = self.dmg * 0.3
            spiderling.color = (100, 30, 150)
            spiderling.xp_reward = 0 # XP vermez
            spiderling.gives_xp = False
            
            game.enemies.append(spiderling)
            game.entity_id_counter += 1
            
    def shoot_web(self, game):
        # Oyuncuyu donduracak bir ağ mermisi (silence/slow etkili)
        p = game.players[game.local_player_id]
        angle = math.atan2(p.y - self.y, p.x - self.x)
        vx = math.cos(angle) * 8
        vy = math.sin(angle) * 8
        # Zehir (poison) tipli bir mermi olarak gönderelim, ama özel tip verebiliriz
        proj = Projectile(game.entity_id_counter, self.x, self.y, vx, vy, self.dmg * 0.2, p_type='web', aoe=50, lifetime=150, is_hostile=True)
        proj.color = (200, 200, 200) # Beyaz ağ
        game.projectiles.append(proj)
        game.entity_id_counter += 1

    def draw(self, screen, camera_x, camera_y):
        # Kraliçe Örümcek Özel Çizimi
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Bacaklar
        time_ms = pygame.time.get_ticks()
        for i in range(8):
            angle = i * (math.pi / 4) + math.sin(time_ms * 0.01 + i) * 0.2
            end_x = draw_x + math.cos(angle) * self.radius * 1.5
            end_y = draw_y + math.sin(angle) * self.radius * 1.5
            pygame.draw.line(screen, (50, 20, 80), (draw_x, draw_y), (end_x, end_y), 6)
            
        # Gövde
        super().draw(screen, camera_x, camera_y)
