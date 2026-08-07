import zipfile
import os

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            # Exclude specific folders
            if 'release_assets' in dirs:
                dirs.remove('release_assets')
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')
            if 'build' in dirs:
                dirs.remove('build')
            if 'dist' in dirs:
                dirs.remove('dist')
            
            for file in files:
                file_path = os.path.join(root, file)
                # Don't zip the output file itself
                if file_path == output_path:
                    continue
                # Don't zip session logs or temp files
                if '.system_generated' in root:
                    continue
                    
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
            
        # dist klasöründeki Boxhead.exe'yi ana dizine kopyalayarak dahil et
        exe_path = os.path.join(folder_path, "dist", "Boxhead.exe")
        if os.path.exists(exe_path):
            zipf.write(exe_path, "Boxhead.exe")
            print("Boxhead.exe pakete dahil edildi!")

if __name__ == "__main__":
    src = "c:\\Users\\PC\\Desktop\\py\\boxhead\\Pygame_Versiyonu"
    dest = "c:\\Users\\PC\\Desktop\\py\\boxhead\\Pygame_Versiyonu\\release_assets\\Boxhead_v1.1.0.zip"
    zip_folder(src, dest)
    print(f"Zip created: {dest}")
