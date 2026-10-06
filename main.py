import os
import urllib.request
import subprocess

# Render, Railway ba Hugging Face theke deya PORT nibe, na paile 7860 (Hugging Face default)
PORT = os.environ.get("PORT", "7860")
TTYD_URL = "https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.x86_64"
TTYD_BIN = "./ttyd"

def setup_vps():
    # TTYD binary na thakle download korbe
    if not os.path.exists(TTYD_BIN):
        print("VPS Terminal setup hocche...")
        try:
            urllib.request.urlretrieve(TTYD_URL, TTYD_BIN)
            os.chmod(TTYD_BIN, 0o755) # Executable permission dicche
        except Exception as e:
            print(f"Error: {e}")
            return

    print(f"VPS on hocche port {PORT} e...")
    
    # Web e Bash shell run korbe (-W mane full access write command)
    # Tui chaile bash er bodole 'sh' ba 'python3' o dite paris
    subprocess.run([TTYD_BIN, "-p", str(PORT), "-W", "bash"])

if __name__ == "__main__":
    setup_vps()
