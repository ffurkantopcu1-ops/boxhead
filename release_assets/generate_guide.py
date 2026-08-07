from PIL import Image, ImageDraw, ImageFont
import os
import random

# --- DATA & MAPS ---
STAT_MAP = {
    'physDmgFlat': 'Fiziksel Hasar', 'dmgMult': 'Hasar Çarpanı (%)', 'fireRate': 'Saldırı Hızı (%)', 'critChance': 'Kritik Şans (%)',
    'armor': 'Zırh', 'maxHp': 'Maksimum Can', 'speed': 'Hareket Hızı', 'magicFind': 'Eşya Bulma Şansı (%)', 'goldGain': 'Altın Kazanımı (%)',
    'lifesteal': 'Can Çalma (%)', 'dodgeChance': 'Sıyrılma Şansı (%)', 'hpRegen': 'Can Yinelenme', 'thorns': 'Dikenler (Geri Hasar)',
    'poisonDps': 'Zehir Hasarı (Saniye)', 'aoe': 'Etki Alanı Çarpanı', 'projectileCount': 'Mermi Sayısı', 'bounce': 'Sekme Sayısı',
    'fireDamage': 'Ateş Hasarı', 'frostDamage': 'Buz Hasarı', 'elementDmgMult': 'Elementer Hasar (%)', 'dotDmgMult': 'Zamanla Hasar (%)',
    'statusDuration': 'Etki Süresi Artışı', 'cooldownReduction': 'Bekleme Süresi Azaltma (%)', 'bossDmgMult': 'Boss Hasarı (%)',
    'armorPen': 'Zırh Delme (%)', 'lowHpExec': 'İnfaz Eşiği (%)', 'killComboDmg': 'Kombo Başına Hasar (%)',
    'meleeRange': 'Yakın Dövüş Menzili', 'shockwave': 'Şok Dalgaları', 'toxicAura': 'Zehirli Aura', 'orbitDrones': 'Savunma Dronları',
    'blackHoleChance': 'Karadelik Şansı', 'dashCooldownReduc': 'Dash Bekleme Süresi Azaltma'
}

COLORS = {
    'bg': (10, 10, 18), 'panel': (25, 25, 40), 'text': (240, 240, 255), 'subtext': (160, 160, 180),
    'unique': (231, 76, 60), 'rare': (241, 196, 15), 'magic': (52, 152, 219), 'broken': (155, 89, 182),
    'fire': (231, 76, 60), 'frost': (52, 152, 219), 'set': (241, 196, 15), 'section': (40, 44, 52)
}

# --- FONTS ---
try:
    font_title = ImageFont.truetype("arial.ttf", 75)
    font_h1 = ImageFont.truetype("arial.ttf", 55)
    font_h2 = ImageFont.truetype("arial.ttf", 40)
    font_p = ImageFont.truetype("arial.ttf", 26)
    font_small = ImageFont.truetype("arial.ttf", 22)
except:
    font_title = font_h1 = font_h2 = font_p = font_small = ImageFont.load_default()

class GuideGenerator:
    def __init__(self):
        self.width = 1800
        self.height = 10000 # High estimation for growth
        self.img = Image.new('RGB', (self.width, self.height), color=COLORS['bg'])
        self.draw = ImageDraw.Draw(self.img)
        self.current_y = 60

    def draw_text(self, text, x, y, font, color=COLORS['text']):
        self.draw.text((x, y), text, font=font, fill=color)

    def draw_section_header(self, title, icon_text=""):
        self.current_y += 100
        header_rect = [50, self.current_y, self.width - 50, self.current_y + 110]
        self.draw.rectangle(header_rect, fill=COLORS['section'], outline=(100, 100, 150), width=3)
        self.current_y += 20
        full_title = f"{icon_text} {title.upper()}" if icon_text else title.upper()
        self.draw_text(full_title, 100, self.current_y, font_h1, color=COLORS['rare'])
        self.current_y += 130

    def draw_controls(self):
        self.draw_section_header("KONTROLLER (CONTROLS)", "🎮")
        controls = [
            ("WASD", "Hareket Etme"),
            ("L-MOUSE", "Saldırı / Ateş Etme"),
            ("SPACE", "Dash (Hızlı Atılma)"),
            ("TAB / I", "Envanter ve Gelişim"),
            ("C", "Crafting Penceresi (Hızlı Erişim)"),
            ("1 - 9", "Yeteneklerin Kullanımı")
        ]
        margin = 150
        for i, (key, desc) in enumerate(controls):
            col = i % 2
            row = i // 2
            x = margin + col * 750
            y = self.current_y + row * 60
            self.draw_text(f"[{key}] :", x, y, font_p, color=COLORS['magic'])
            self.draw_text(desc, x + 250, y, font_p)
        self.current_y += (len(controls) // 2 + 1) * 70

    def draw_mechanics(self):
        self.draw_section_header("YENİ MEKANİKLER & EKONOMİ", "💠")
        mechanics = [
            ("🔥 KABUS AI", "Impossible ve Very Hard zorluklarda düşmanlar artık mesafe fark etmeksizin ateş ederler!"),
            ("🏃 OKÇU DASH", "Okçular (Archerlar) tehlike anında Dash atarak sizden uzaklaşabilirler."),
            ("💰 EKONOMİ", "Eşya fiyatları güncellendi; UNIQUE (5000 G), RARE (2000 G), MAGIC (250 G), NORMAL (50 G)."),
            ("📈 GELİŞİM", "Saldırı Hızı (AS) sınırı 5'e indirildi. Menzil bonusu (+12/lvl) büyük oranda artırıldı."),
            ("🛒 OTO-SATIŞ", "Kümülatif sistem; seçilen nadirlik ve altındaki tüm eşyalar otomatik olarak satılır.")
        ]
        margin = 150
        for title, desc in mechanics:
            self.draw_text(title, margin, self.current_y, font_h2, color=COLORS['unique'])
            self.draw_text(desc, margin + 40, self.current_y + 50, font_p, color=COLORS['subtext'])
            self.current_y += 120

    def draw_classes(self):
        self.draw_section_header("SINIFLAR VE ÖZELLİKLERİ (CLASSES)", "🥋")
        classes = [
            ("SAVAŞÇI (Warrior)", "Yüksek Dayanıklılık: +20% Can, +20% Hasar çarpanı. Tank bazlı oyun tarzı."),
            ("NİNJA (Ninja)", "Hızın Efendisi: +30% Saldırı Hızı, +25% Kaçınma, En yüksek hareket hızı (6.0)."),
            ("KESKİN NİŞANCI (Sniper)", "Ölümcül Vuruşlar: +50% Hasar Çarpanı, +20% Kritik Şans. Uzun menzilli hakimiyet."),
            ("SİMYACI (Alchemist)", "Alan Kontrolü: +40% Etki Alanı (AoE), +30% Zehir Hasarı (DoT). Kitle imha."),
            ("MİNYON EFENDİSİ (Beastmaster)", "Ordu Gücü: Minyon hasarını ve canını ciddi oranda artırır."),
            ("MÜHENDİS (Engineer)", "Savunma Hattı: +10 Zırh, Taret kurma yeteneği ve teknolojik destek.")
        ]
        margin = 150
        for title, desc in classes:
            self.draw_text(title, margin, self.current_y, font_h2, color=COLORS['magic'])
            self.draw_text(desc, margin + 40, self.current_y + 50, font_p, color=COLORS['subtext'])
            self.current_y += 120

    def add_orbs(self, orbs):
        self.draw_section_header("SİHİRLİ KÜRELER (ORBS)", "🔮")
        margin = 150
        for orb in orbs:
            box = [margin, self.current_y, self.width - margin, self.current_y + 120]
            self.draw.rectangle(box, fill=COLORS['panel'], outline=(80, 80, 110), width=2)
            
            name = orb['name']
            desc = orb['desc']
            price = f"{orb['price']} G"
            rarity_color = COLORS['unique'] if orb['rarity'] == 'Unique' else COLORS['rare']
            
            self.draw_text(name, margin + 30, self.current_y + 20, font_h2, color=rarity_color)
            self.draw_text(f"Fiyat: {price}", self.width - margin - 350, self.current_y + 25, font_p, color=(100, 255, 100))
            self.draw_text(desc, margin + 40, self.current_y + 75, font_p, color=COLORS['subtext'])
            self.current_y += 140

    def add_sets(self, sets):
        self.draw_section_header("EFSANEVİ SETLER (SET BONUSES)", "⚜️")
        margin = 150
        idx = 0
        x_list = [margin, margin + 800]
        start_y = self.current_y
        max_y = start_y

        for s_id, s_info in sets.items():
            if idx >= 14: break # Safety limit for current layout
            col = idx % 2
            curr_x = x_list[col]
            curr_y = start_y + (idx // 2) * 350
            
            box = [curr_x, curr_y, curr_x + 720, curr_y + 320]
            self.draw.rectangle(box, fill=COLORS['panel'], outline=COLORS['set'], width=3)
            self.draw_text(s_info['name'], curr_x + 30, curr_y + 25, font_h2, color=COLORS['set'])
            
            sub_y = curr_y + 90
            for count, bonus in s_info['bonuses'].items():
                bonus_str = ", ".join([f"{STAT_MAP.get(k, k)} +{v}" for k, v in bonus.items()])
                self.draw_text(f"({count} Parça):", curr_x + 30, sub_y, font_small, color=(180, 180, 255))
                self.draw_text(bonus_str, curr_x + 160, sub_y, font_small)
                sub_y += 50
            
            idx += 1
            max_y = max(max_y, curr_y + 370)

        self.current_y = max_y

    def add_affixes(self, affixes):
        self.draw_section_header("PREFIX & SUFFIX ÖZELLİKLERİ", "⚔️")
        margin = 150
        
        # Prefixes
        self.draw_text("PREFIXES (İsimden Önce Gelenler)", margin, self.current_y, font_h2, color=COLORS['magic'])
        self.current_y += 70
        p_list = affixes['prefixes']
        for i, p in enumerate(p_list):
            tx = margin + (i % 3) * 550
            ty = self.current_y + (i // 3) * 55
            self.draw_text(f"• {p['name']}: {STAT_MAP.get(p['stat'], p['stat'])}", tx, ty, font_p)
        self.current_y += (len(p_list) // 3 + 2) * 60

        # Suffixes
        self.draw_text("SUFFIXES (İsimden Sonra Gelenler)", margin, self.current_y, font_h2, color=COLORS['rare'])
        self.current_y += 70
        s_list = affixes['suffixes']
        for i, s in enumerate(s_list):
            tx = margin + (i % 3) * 550
            ty = self.current_y + (i // 3) * 55
            self.draw_text(f"• {s['name']}: {STAT_MAP.get(s['stat'], s['stat'])}", tx, ty, font_p)
        self.current_y += (len(s_list) // 3 + 2) * 65

    def add_broken(self, broken):
        self.draw_section_header("KIRIK ÖZELLİKLER (BROKEN STATS)", "🌌")
        margin = 150
        desc = "Sadece Özel Küre (Special Orb) veya Lanetli Eşyalarla gelebilen ultra nadir güçler:"
        self.draw_text(desc, margin, self.current_y, font_p, color=COLORS['subtext'])
        self.current_y += 80

        for b in broken:
            box = [margin, self.current_y, self.width - margin, self.current_y + 80]
            self.draw.rectangle(box, fill=(20, 20, 35), outline=COLORS['broken'], width=2)
            self.draw_text(b['name'], margin + 40, self.current_y + 20, font_h2, color=COLORS['broken'])
            self.draw_text(f"➥ {STAT_MAP.get(b['stat'], b['stat'])} (Maksimum Ölçeklenme)", margin + 500, self.current_y + 25, font_p)
            self.current_y += 100

    def generate(self):
        # --- HEADER ---
        self.draw.rectangle([0, 0, self.width, 350], fill=(15, 15, 30))
        self.draw_text("BOXHEAD 2.0: KABUS VE REFAH", self.width // 2 - 620, 80, font_title, color=COLORS['rare'])
        self.draw_text("RESMİ OYUNCU REHBERİ (OFFICIAL PLAYER GUIDE) - v1.0.6.2", self.width // 2 - 420, 190, font_h2, color=COLORS['subtext'])
        self.current_y = 400

        # Import ItemSystem context
        from logic.item_system import ItemSystem
        sys_obj = ItemSystem()

        # Build blocks
        self.draw_controls()
        self.draw_mechanics()
        self.draw_classes()
        self.add_orbs(sys_obj.orbs)
        self.add_sets(sys_obj.set_types)
        self.add_affixes(sys_obj.affixes)
        self.add_broken(sys_obj.affixes['broken'])
        
        # FINAL CROP & SAVE
        final_h = self.current_y + 150
        
        # Siyahlık hatasını önlemek için önce kalan alanı arkaplan rengiyle doldur
        self.draw.rectangle([0, self.current_y, self.width, final_h], fill=COLORS['bg'])
        
        # Ardından tam boyutta kırp
        self.img = self.img.crop((0, 0, self.width, final_h))
        
        self.img.save("guide.png")
        print(f"RESMİ REHBER OLUŞTURULDU: guide.png ({self.width}x{final_h})")

if __name__ == "__main__":
    import sys
    sys.path.append(os.getcwd())
    gen = GuideGenerator()
    gen.generate()
