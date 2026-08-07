import os
import py_compile
import sys

def check_syntax(directory):
    errors = []
    print(f"Scanning {directory}...")
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(str(e))
    return errors

if __name__ == "__main__":
    base_dir = "."
    all_errors = check_syntax(base_dir)
    
    if all_errors:
        print("\n[HATA] Bulunan Yazım Hataları:")
        for err in all_errors:
            print("-" * 30)
            print(err)
        sys.exit(1)
    else:
        print("\n[BAŞARILI] Tüm dosyalar hatasız derleniyor.")
        sys.exit(0)
