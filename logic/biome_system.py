import random

class BiomeSystem:
    """Biyom sistemi - Her 10 wave'de dünya değişir."""

    # ZEMİN PALETİ — tüketim noktası: tile_renderer._palette (prosedürel karo
    # üretimi). Bu alanlar uzun süre ÖLÜ veriydi: zemini çizen kod biome id'sini
    # GameLogic.BIOMES'te (normal/desert/volcano/dark) arıyordu, buradaki
    # id'lerle (forest/lava/ice/void) yalnızca "ice" eşleşiyordu; diğer tüm
    # dalgalarda sabit gri bir zemin çiziliyordu. O tablo kaldırıldı, tek
    # doğruluk kaynağı burası.
    #
    # Renkler ayrıca AÇILDI: eski değerler (20,35,20) gibi neredeyse siyahtı;
    # prosedürel doku/dekor o koyulukta hiç okunmuyordu. Yeni değerler
    # orta-koyu — varlıklar (parlak sınıf renkleri) hâlâ zeminden ayrışıyor.
    # accent_color dekor ve yama rengini besler.
    BIOMES = {
        "forest": {
            "name": "🌲 Karanlık Orman",
            "desc": "Yoğun ağaçlar ve gölgeler",
            "floor_color_1": (64, 78, 54),
            "floor_color_2": (76, 92, 62),
            "grid_line_color": (28, 38, 26),
            "accent_color": (86, 116, 58),
            "waves": (1, 10),
            "enemy_bonus": {"speed": 1.1},  # Orman düşmanları biraz hızlı
            "hazards": ["poison_pool", "thorn_bush"],
            "ambient_color": (0, 30, 0, 40),  # Yeşil sis
            "music_mood": "tense"
        },
        "lava": {
            "name": "🌋 Volkan Vadisi",
            "desc": "Lav akıntıları ve ateş yağmuru",
            "floor_color_1": (78, 54, 46),
            "floor_color_2": (94, 64, 52),
            "grid_line_color": (36, 22, 18),
            "accent_color": (168, 72, 28),
            "waves": (11, 20),
            "enemy_bonus": {"dmg": 1.2, "fire_resist": True},
            "hazards": ["lava_pool", "fire_rain"],
            "ambient_color": (40, 10, 0, 30),  # Kırmızı sis
            "music_mood": "intense"
        },
        "ice": {
            "name": "❄️ Buzul Çölü",
            "desc": "Kaygan zeminler ve buz fırtınaları",
            "floor_color_1": (76, 90, 112),
            "floor_color_2": (90, 106, 128),
            "grid_line_color": (52, 64, 84),
            "accent_color": (166, 198, 224),
            "waves": (21, 30),
            "enemy_bonus": {"hp": 1.3, "frost_aura": True},
            "hazards": ["ice_patch", "blizzard"],
            "ambient_color": (0, 10, 40, 35),  # Mavi sis
            "music_mood": "epic"
        },
        "void": {
            "name": "🌑 Boşluk",
            "desc": "Boyutlar arası karanlık",
            "floor_color_1": (56, 46, 78),
            "floor_color_2": (70, 58, 94),
            "grid_line_color": (26, 20, 40),
            "accent_color": (140, 88, 186),
            "waves": (31, 99),
            "enemy_bonus": {"hp": 1.5, "dmg": 1.3, "teleport": True},
            "hazards": ["void_rift", "shadow_zone"],
            "ambient_color": (20, 0, 30, 45),  # Mor sis
            "music_mood": "dread"
        }
    }
    
    # Biome-specific hazard definitions
    HAZARD_TYPES = {
        "poison_pool": {
            "name": "Zehir Gölü",
            "color": (50, 180, 50),
            "radius": 80,
            "dps": 8,
            "duration": 15.0,
            "effect": "poison"
        },
        "thorn_bush": {
            "name": "Dikenli Çalı",
            "color": (80, 120, 40),
            "radius": 50,
            "dps": 5,
            "duration": 999,  # Permanent
            "effect": "slow",
            "slow_mult": 0.5
        },
        "lava_pool": {
            "name": "Lav Gölü",
            "color": (220, 80, 20),
            "radius": 100,
            "dps": 20,
            "duration": 20.0,
            "effect": "burn"
        },
        "fire_rain": {
            "name": "Ateş Yağmuru",
            "color": (255, 120, 30),
            "radius": 60,
            "dps": 15,
            "duration": 5.0,
            "effect": "burn",
            "moves": True  # Falls from random positions
        },
        "ice_patch": {
            "name": "Buz Zemin",
            "color": (150, 200, 255),
            "radius": 120,
            "dps": 0,
            "duration": 999,
            "effect": "slide",  # Player slides (momentum)
            "slide_mult": 1.5
        },
        "blizzard": {
            "name": "Kar Fırtınası",
            "color": (200, 220, 255),
            "radius": 200,
            "dps": 3,
            "duration": 8.0,
            "effect": "slow",
            "slow_mult": 0.6
        },
        "void_rift": {
            "name": "Boşluk Yarığı",
            "color": (100, 0, 150),
            "radius": 70,
            "dps": 25,
            "duration": 10.0,
            "effect": "teleport_random"  # Teleports player randomly
        },
        "shadow_zone": {
            "name": "Gölge Bölgesi",
            "color": (30, 0, 50),
            "radius": 150,
            "dps": 0,
            "duration": 12.0,
            "effect": "blind",  # Reduces visibility
            "visibility_mult": 0.4
        }
    }
    
    def __init__(self):
        self.current_biome_id = "forest"

    def get_biome_for_wave(self, wave_level):
        """Wave seviyesine göre aktif biyomu döndürür."""
        for biome_id, biome in self.BIOMES.items():
            if biome['waves'][0] <= wave_level <= biome['waves'][1]:
                return biome_id, biome
        return 'void', self.BIOMES['void']
    
    def update_biome(self, wave_level):
        """Wave değiştiğinde biyomu güncelle."""
        new_id, new_biome = self.get_biome_for_wave(wave_level)
        if new_id != self.current_biome_id:
            self.current_biome_id = new_id
            return new_biome  # Return new biome for visual update
        return None
    
    def apply_enemy_bonus(self, enemy, wave_level):
        """Biyom bonuslarını düşmana uygula."""
        _, biome = self.get_biome_for_wave(wave_level)
        bonus = biome.get('enemy_bonus', {})
        if 'speed' in bonus:
            enemy.speed *= bonus['speed']
        if 'dmg' in bonus:
            enemy.dmg *= bonus['dmg']
        if 'hp' in bonus:
            enemy.max_hp *= bonus['hp']
            enemy.hp = enemy.max_hp
        if bonus.get('fire_resist'):
            enemy.fire_resist = True
        if bonus.get('frost_aura'):
            # frost_aura tüketim noktası: entities/enemy.py -> update()
            # (200 piksel içindeki oyuncuyu yavaşlatır). Aynı bayrağı
            # elite_system de kurar.
            enemy.frost_aura = True
        if bonus.get('teleport'):
            enemy.can_teleport = True

        # Zorluk degisimi base_* uzerinden yeniden hesapladigi icin biyom
        # bonuslari siliniyordu (H4)
        enemy.base_max_hp = enemy.max_hp
        enemy.base_dmg = enemy.dmg
        enemy.base_speed = enemy.speed
    
    def get_random_hazard(self, wave_level):
        """Biyoma uygun rastgele bir tehlike türü döndürür."""
        _, biome = self.get_biome_for_wave(wave_level)
        hazard_ids = biome.get('hazards', [])
        if not hazard_ids:
            return None
        hazard_id = random.choice(hazard_ids)
        return self.HAZARD_TYPES.get(hazard_id)
