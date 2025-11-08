import requests
import json
import traceback
import os
import time
import secrets

# Alamat server Ollama remote
OLLAMA_HOST = "http://10.9.23.2:11434"

def ringkas_teks(teks, model="llama3.2", source_filename=None):
    if not teks.strip():
        return "Tidak ada transkripsi yang terdeteksi"
    
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": model,
        "prompt": f"""
Kamu adalah asisten medis, yang membantu dokter meringkas percakapan dengan pasien.
Berdasarkan format SOAP.

- Tugasmu adalah meringkas teks percakapan antara dokter dan pasien.
- Jangan berasumsi atau menambahkan informasi yang tidak ada dalam teks percakapan.
- Jika ada informasi yang tidak disebutkan dalam teks percakapan, isikan dengan "-".
- Ringkas teks percakapan dalam format berikut:
    Keluhan utama: ...
    Riwayat penyakit: ...
    Sosial Budaya: ...
    Tekanan Darah: ... (format berupa '120/80' tanpa satuan)
    Nadi: ... (format berupa angka, misal '72' tanpa satuan)
    Suhu: ... (format berupa angka, misal '36.5' tanpa satuan)
    Frekuensi Nafas: ... (format berupa angka, misal '20' tanpa satuan)
    Berat Badan: ... (format berupa angka, misal '70' tanpa satuan)
    Asesmen: ...
    Plan: ...
- Gunakan bahasa Indonesia yang profesional dan jelas.
- Format pengisian singkat dan tanpa tambahan penjelasan.
- Jangan tambahkan penjelasan lain di luar format yang diminta.

Teks Percakapan:
{teks}
"""
    }
    try:
        print("[INFO] Mengirim permintaan ringkasan ke Ollama...")
        response = requests.post(url, json=payload, stream=True, timeout=300)

        if response.status_code != 200:
            raise RuntimeError(f"Gagal merangkum teks: {response.text}")

        ringkasan = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        ringkasan += data["response"]
                except json.JSONDecodeError:
                    continue

        ringkasan = ringkasan.strip() if ringkasan else "Tidak ada balasan dari model."

        try:
            print("======================================================")
            print("[RESULT] Ringkasan dari Ollama:")
            print(ringkasan)
            print("======================================================")
        except Exception:
            pass

        try:
            tools_dir = os.path.dirname(__file__)
            project_dir = os.path.abspath(os.path.join(tools_dir, ".."))
            uploads_dir = os.path.join(project_dir, "uploads/ringkasan")
            os.makedirs(uploads_dir, exist_ok=True)

            if source_filename:
                base = os.path.splitext(os.path.basename(source_filename))[0]
                outname = f"{base}.txt"
                outpath = os.path.join(uploads_dir, outname)
                # avoid accidental overwrite
                if os.path.exists(outpath):
                    timecode = f"{int(time.time()*1000)}-{secrets.token_hex(3)}"
                    outname = f"{base}-{timecode}.txt"
                    outpath = os.path.join(uploads_dir, outname)
            else:
                timecode = f"{int(time.time()*1000)}-{secrets.token_hex(3)}"
                outname = f"ringkasan-{timecode}.txt"
                outpath = os.path.join(uploads_dir, outname)

            with open(outpath, "w", encoding="utf-8") as of:
                of.write(ringkasan)

            print(f"[INFO] Ringkasan disimpan ke: {outpath}")
        except Exception as e:
            print("[WARN] Gagal menyimpan ringkasan ke uploads:", e)

        return ringkasan

    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"Gagal menghubungi Ollama: {str(e)}")

def parse_ringkasan(ringkasan):
    keluhan = ""
    riwayat = ""
    sosial = ""
    # kejiwaan = ""
    tekananDarah = ""
    nadi = ""
    suhu = ""
    frekuensiNafas = ""
    beratBadan = ""
    assesmen = ""
    plan = ""

    for line in ringkasan.splitlines():
        if "Keluhan utama" in line:
            keluhan = line.split(":", 1)[1].strip()
        elif "Riwayat" in line:
            riwayat = line.split(":", 1)[1].strip()
        elif "Sosial" in line:
            sosial = line.split(":", 1)[1].strip()
        # elif "Kejiwaan" in line:
            # kejiwaan = line.split(":", 1)[1].strip()
        elif "Tekanan Darah" in line:
            tekananDarah = line.split(":", 1)[1].strip()
        elif "Nadi" in line:
            nadi = line.split(":", 1)[1].strip()
        elif "Suhu" in line:
            suhu = line.split(":", 1)[1].strip()
        elif "Frekuensi Nafas" in line:
            frekuensiNafas = line.split(":", 1)[1].strip()
        elif "Berat Badan" in line:
            beratBadan = line.split(":", 1)[1].strip()
        elif "Asesmen" in line:
            assesmen = line.split(":", 1)[1].strip()
        elif "Plan" in line:
            plan = line.split(":", 1)[1].strip()
            
    dataInput = {
        "keluhan": keluhan,
        "riwayat": riwayat,
        "sosial": sosial,
        # "kejiwaan": kejiwaan,
        "tekananDarah": tekananDarah,
        "nadi": nadi,
        "suhu": suhu,
        "frekuensiNafas": frekuensiNafas,
        "beratBadan": beratBadan,
        "assesmen": assesmen,
        "plan": plan,
    }

    return dataInput

# - Ringkas percakapan dalam format berikut:
    # Keluhan utama: ...
    # Riwayat penyakit: ...
    # Sosial Budaya: ...
    # Kondisi Kejiwaan: ... (format Tenang, Gelisah/Takut, Marah/Stres, atau Lainnya [pilih salah satu])
    # Tekanan Darah: ... (format berupa 120/80)
    # Nadi: ... (format berupa angka, misal 72)
    # Suhu: ... (format berupa angka, misal 36.5)
    # Frekuensi Nafas: ... (format berupa angka, misal 20)
    # Berat Badan: ... (format berupa angka, misal 70)
    # Asesmen: ...
    # Plan: ...