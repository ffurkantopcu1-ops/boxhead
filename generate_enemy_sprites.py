"""
Orc spritesheetinden tam karakterleri otomatik tespit ederek düşman sprite'ları üretir.
Karakter başına satır: 6 satır (her satır bir yön/aksiyon)
Sütunlar: animasyon kareleri
"""
import os
from PIL import Image

ASSETS = 'public/assets'
os.makedirs(ASSETS, exist_ok=True)

def find_content_rows(img):
    """Transparan olmayan satır gruplarını bul."""
    pixels = img.load()
    w, h = img.size
    groups = []
    in_g = False
    start = 0
    for y in range(h):
        has = any(pixels[x, y][3] > 10 for x in range(w))
        if has and not in_g:
            in_g = True; start = y
        elif not has and in_g:
            in_g = False; groups.append((start, y))
    if in_g:
        groups.append((start, h))
    return groups

def find_content_cols_in_row(img, row_start, row_end):
    """Belirli bir satır bandındaki sütun gruplarını bul."""
    pixels = img.load()
    w = img.size[0]
    groups = []
    in_g = False
    start = 0
    for x in range(w):
        has = any(pixels[x, y][3] > 10 for y in range(row_start, row_end))
        if has and not in_g:
            in_g = True; start = x
        elif not has and in_g:
            in_g = False; groups.append((start, x))
    if in_g:
        groups.append((start, w))
    return groups

def extract_char_frame(img, row_start, row_end, col_start, col_end, padding=4):
    """Tek bir karakter karesini çıkar, padding ekle."""
    rs = max(0, row_start - padding)
    re = min(img.size[1], row_end + padding)
    cs = max(0, col_start - padding)
    ce = min(img.size[0], col_end + padding)
    return img.crop((cs, rs, ce, re)).convert("RGBA")

def colorize_rgba(img, r_mul, g_mul, b_mul, brightness=1.0):
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for x in range(w):
        for y in range(h):
            r, g, b, a = pixels[x, y]
            if a > 10:
                nr = min(255, int(r * r_mul * brightness))
                ng = min(255, int(g * g_mul * brightness))
                nb = min(255, int(b * b_mul * brightness))
                pixels[x, y] = (nr, ng, nb, a)
    return img

def make_enemy(sheet, base_name, r_mul, g_mul, b_mul, brightness=1.0, size=96):
    """Spritesheet'ten otomatik karakter tespiti ile düşman sprite'ları üret."""
    # Satır gruplarını bul (her satır = 1 yön)
    row_groups = find_content_rows(sheet)
    print(f"  {base_name}: {len(row_groups)} satır bulundu")
    
    # Yön eşleştirmesi — LPC/RPG Maker standartı:
    # Satır 0=aşağı, 1=sol, 2=sağ, 3=yukarı (bazı şeetlerde farklı)
    dir_map = {0: 'down', 1: 'left', 2: 'right', 3: 'up'}
    
    for row_idx, (r_start, r_end) in enumerate(row_groups[:4]):
        direction = dir_map.get(row_idx, f'dir{row_idx}')
        
        # Bu satırdaki ilk karakteri bul
        col_groups = find_content_cols_in_row(sheet, r_start, r_end)
        if not col_groups:
            continue
        
        # İlk animasyon karesini al
        c_start, c_end = col_groups[0]
        frame = extract_char_frame(sheet, r_start, r_end, c_start, c_end, padding=3)
        
        colored = colorize_rgba(frame, r_mul, g_mul, b_mul, brightness)
        scaled = colored.resize((size, size), Image.LANCZOS)
        path = f"{ASSETS}/enemy_{base_name}_{direction}.png"
        scaled.save(path, "PNG")
    
    print(f"  → {base_name} tamamlandı")

# Spritesheet'leri yükle
orc  = Image.open('orc.png').convert("RGBA")
orc2 = Image.open('orc_v2.png').convert("RGBA")

print("Düşman sprite'ları üretiliyor...")

# ---- DÜŞMAN TÜRLERİ ----
make_enemy(orc,  'normal',   1.0, 1.0, 1.0,  brightness=1.0,  size=96)
make_enemy(orc2, 'tank',     0.9, 0.4, 1.4,  brightness=0.9,  size=128)
make_enemy(orc,  'archer',   0.4, 0.7, 1.5,  brightness=1.1,  size=88)
make_enemy(orc2, 'suicide',  1.6, 0.5, 0.3,  brightness=1.1,  size=80)
make_enemy(orc,  'summoner', 1.4, 1.2, 0.2,  brightness=1.0,  size=110)
make_enemy(orc2, 'dasher',   0.3, 1.3, 1.2,  brightness=1.15, size=88)
make_enemy(orc,  'splitter', 0.8, 0.2, 1.0,  brightness=0.75, size=140)
make_enemy(orc2, 'megaboss', 1.8, 0.1, 0.1,  brightness=0.9,  size=200)

print("\nTüm sprite'lar oluşturuldu!")
