import os
import subprocess
import traceback
import requests
from glob import glob

# Path dasar
TOOLS_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.abspath(os.path.join(TOOLS_DIR, ".."))
UPLOAD_DIR = os.path.join(PROJECT_DIR, "uploads")
SCRIPTS_DIR = os.path.join(UPLOAD_DIR, "transkrip")
os.makedirs(UPLOAD_DIR, exist_ok=True)  

# Path whisper & model
WHISPER_PATH = os.path.join(PROJECT_DIR, "build", "whisper")
MODEL_PATH = os.path.join(PROJECT_DIR, "models", "ggml-small.bin")

def transkrip_audio(upload_file=None):
    """
    Jika upload_file diberikan, gunakan file tersebut.
    Jika tidak, ambil file .webm terbaru di folder uploads.
    """
    try:
        # === Tentukan file input ===
        if upload_file:
            filename = os.path.basename(upload_file.filename) if upload_file.filename else f"rekaman-{int(os.times()[4]*1000)}.webm"
            input_path = os.path.join(UPLOAD_DIR, filename)
            os.makedirs(os.path.dirname(input_path) or UPLOAD_DIR, exist_ok=True)
            with open(input_path, "wb") as f:
                f.write(upload_file.file.read())
            print(f"[INFO] File diterima: {input_path}")
        else:
            list_files = glob(os.path.join(UPLOAD_DIR, "*.webm"))
            if not list_files:
                return "[ERROR] Tidak ada file .webm di folder uploads"
            input_path = max(list_files, key=os.path.getmtime)
            print(f"[INFO] Menggunakan file .webm terbaru: {input_path}")

        # === Konversi ke WAV ===
        basename = os.path.splitext(os.path.basename(input_path))[0]
        wav_path = os.path.join(UPLOAD_DIR, f"{basename}.wav")
        txt_path = os.path.join(SCRIPTS_DIR, f"{basename}")

        ffmpeg_cmd = [
            "ffmpeg", 
            "-i", input_path, 
            "-ar", "16000", 
            "-ac", "1", 
            "-y", wav_path
            ]
        subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"[INFO] File audio siap untuk transkripsi: {wav_path}")

        # === Jalankan Whisper ===
        whisper_cmd = [
            WHISPER_PATH,
            "-f", wav_path,
            "--model", MODEL_PATH,
            "--language", "id",
            "--output-txt", "",
            "--output-file", txt_path,
            "-nt"
        ]

        print(f"[INFO] Menjalankan Whisper: {' '.join(whisper_cmd)}")
        result = subprocess.run(
            whisper_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        # === Ambil hasil dari file output ===
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                teks = f.read().strip()
        else:
            teks = result.stdout.strip()

        if not teks:
            print("[WARN] Tidak ada hasil transkripsi yang terdeteksi.")
            return "[GAGAL] Whisper tidak menghasilkan teks apa pun."


        print("======================================================")
        print(f"[RESULT] Hasil transkrip untuk '{os.path.basename(wav_path)}':")
        print(teks)
        print("======================================================")
        print("[INFO] Transkrip selesai.")
        return teks

    except subprocess.CalledProcessError as e:
        print("[ERROR] Whisper CLI gagal:")
        print(e.stderr)
        return f"[GAGAL] {e.stderr}"
    except Exception as e:
        print("[ERROR] Terjadi kesalahan saat transkripsi:")
        traceback.print_exc()
        return f"[GAGAL] {e}"