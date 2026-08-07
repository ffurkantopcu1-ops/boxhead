import os
from PIL import Image

def process_images():
    assets_dir = 'public/assets'
    for filename in os.listdir(assets_dir):
        if not filename.endswith('.png'):
            continue
        # Karakter, ikon ve düşman sprite'larını işle
        if (filename.startswith('char_') or 
            filename.startswith('icon_') or 
            filename.startswith('enemy_')):
            
            filepath = os.path.join(assets_dir, filename)
            img = Image.open(filepath).convert("RGBA")
            data = list(img.getdata())
            
            cleaned = []
            for r, g, b, a in data:
                # Yarı şeffaf kenar pikselleri: alpha < 128 ise tamamen şeffaf yap
                if a < 128:
                    cleaned.append((0, 0, 0, 0))
                else:
                    cleaned.append((r, g, b, 255))
                    
            img.putdata(cleaned)
            img.save(filepath, "PNG")
            print(f"Cleaned: {filename}")

if __name__ == "__main__":
    process_images()
