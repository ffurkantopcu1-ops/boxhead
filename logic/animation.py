import pygame

class DirectionalAnimation:
    def __init__(self, spritesheet_path, frame_width=64, frame_height=64):
        # Şeffaf resmi yükle
        self.sheet = pygame.image.load(spritesheet_path).convert_alpha()
        
        # Tüm karakter kutucuklarını bul
        mask = pygame.mask.from_surface(self.sheet)
        all_rects = mask.get_bounding_rects()
        
        # Filtrele: Sadece karakter boyutundaki kutuları al (Boyu > 100px olanlar gerçek karakterdir)
        # Yazıları ("Walk Down" vb.) boyu kısa olduğu için filtreliyoruz.
        char_rects = []
        for r in all_rects:
            if r.height > 100 and r.width > 30:
                # Eğer kutu çok genişse (Birden fazla karakter birleşmişse) böl!
                if r.width > 280:
                    num_split = round(r.width / 170)
                    w_split = r.width // num_split
                    for j in range(num_split):
                        char_rects.append(pygame.Rect(r.x + j*w_split, r.y, w_split, r.height))
                else:
                    char_rects.append(r)
        
        # Y koordinatına göre sırala
        char_rects.sort(key=lambda r: r.y)
        
        # Satırları gruplandır (Y farkı 100px'den fazlaysa yeni satır)
        rows = []
        if char_rects:
            current_row = [char_rects[0]]
            for i in range(1, len(char_rects)):
                if char_rects[i].y - current_row[-1].y > 100:
                    rows.append(sorted(current_row, key=lambda r: r.x))
                    current_row = [char_rects[i]]
                else:
                    current_row.append(char_rects[i])
            rows.append(sorted(current_row, key=lambda r: r.x))

        # 4 Yön: 0: Down, 1: Up, 2: Left, 3: Right
        self.animations = {0: [], 1: [], 2: [], 3: []}
        
        # Satırları eşleştir (AI kağıtları genelde: Down, Up, Left, Right sırasındadır)
        # Eğer 4'ten fazla satır varsa ilk 4'ü alıyoruz
        for i, row_rects in enumerate(rows[:4]):
            for rect in row_rects:
                # Orijinal resimden karakteri kes
                frame = self.sheet.subsurface(rect).convert_alpha()
                self.animations[i].append(frame)
        
        # Eğer bir yön boş kaldıysa (tespit edilemediyse) Down yönünü kopyala
        for i in range(4):
            if not self.animations[i] and self.animations[0]:
                self.animations[i] = self.animations[0]

        self.current_direction = 0
        self.frame_index = 0
        self.timer = 0
        self.fps = 10
        self.is_moving = False

    def update(self, dt, is_moving, angle):
        self.is_moving = is_moving
        
        # Açıya göre yön belirle
        if 0.78 < angle <= 2.36:
            self.current_direction = 0 # Down
        elif -2.36 < angle <= -0.78:
            self.current_direction = 1 # Up
        elif -0.78 < angle <= 0.78:
            self.current_direction = 3 # Right
        else:
            self.current_direction = 2 # Left

        if self.is_moving:
            self.timer += dt
            if self.timer >= 1.0 / self.fps:
                self.timer = 0
                anim = self.animations[self.current_direction]
                if anim:
                    self.frame_index = (self.frame_index + 1) % len(anim)
        else:
            self.frame_index = 0

    def get_current_frame(self):
        anim = self.animations[self.current_direction]
        if not anim:
            return None
        return anim[self.frame_index % len(anim)] if anim else None
