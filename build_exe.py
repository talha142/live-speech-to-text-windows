import PyInstaller.__main__
import os
import shutil

# Build command for PyInstaller
# Note: --noconsole is used for GUI apps, but during testing we might keep it
def build_exe():
    print("Starting build process...")
    
    # Define paths
    curr_dir = os.path.abspath(".")
    model_path = os.path.join(curr_dir, "models")
    config_path = os.path.join(curr_dir, "config.yaml")
    
    # PyInstaller arguments
    args = [
        'main.py',
        '--name=RetroSTT',
        '--windowed', # Hide console
        '--onefile',   # Single executable
        f'--add-data={model_path};models',      # Bundle models
        f'--add-data={config_path};.',          # Bundle config
        '--clean',
        '--noconfirm'
    ]
    
    # Also need to bundle pywhispercpp DLLs if they aren't auto-detected
    # Usually pyinstaller handles it if they are in site-packages
    
    print(f"Running PyInstaller with args: {' '.join(args)}")
    PyInstaller.__main__.run(args)
    print("Build complete. Check the 'dist' folder.")

if __name__ == "__main__":
    build_exe()
