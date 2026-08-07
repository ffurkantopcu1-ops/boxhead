import os
from rembg import remove
from PIL import Image

def process_images():
    assets_dir = 'public/assets'
    targets = ['char_', 'icon_']
    for filename in os.listdir(assets_dir):
        if any(filename.startswith(t) for t in targets) and filename.endswith('.png'):
            filepath = os.path.join(assets_dir, filename)
            try:
                input_image = Image.open(filepath).convert("RGBA")
                output_image = remove(input_image)
                output_image.save(filepath, "PNG")
                print(f"OK: {filename}")
            except Exception as e:
                print(f"ERR {filename}: {e}")

if __name__ == "__main__":
    process_images()
