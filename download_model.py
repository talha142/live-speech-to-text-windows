import urllib.request
import os
import sys

def download_model(model_name="base.en"):
    url = f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-{model_name}.bin"
    dest = f"models/ggml-{model_name}.bin"
    
    if os.path.exists(dest):
        print(f"Model {dest} already exists.")
        return
        
    print(f"Downloading {model_name} model from {url}...")
    try:
        urllib.request.urlretrieve(url, dest, reporthook=progress_bar)
        print(f"\nDownloaded model to {dest}")
    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)

def progress_bar(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = downloaded * 100 / total_size
        sys.stdout.write(f"\rProgress: {percent:.2f}%")
        sys.stdout.flush()

if __name__ == "__main__":
    if not os.path.exists("models"):
        os.makedirs("models")
    download_model()
