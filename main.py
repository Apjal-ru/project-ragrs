from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tools.transkrip import transkrip_audio
from tools.ringkas import ringkas_teks, parse_ringkasan
from tools.isi_form import isi_form
import traceback

app = FastAPI()

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Serve uploads directory (read-only) so frontend can fetch saved form JSONs and summaries
app.mount("/uploads/parse", StaticFiles(directory="uploads/parse"), name="uploads")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("soap_global.html", {"request": request})
    
@app.post("/transkrip")
async def proses(file: UploadFile = File(...)):
    try:
        # Transkripsi audio
        teks = transkrip_audio(file)

        # Jika tidak ada teks, hentikan proses dan kembalikan error
        if not teks:
            return JSONResponse({"error": "Tidak ada hasil transkripsi."}, status_code=400)

        # Jika transkrip mengembalikan pesan kesalahan dari helper, jangan lanjut ke ringkas
        if isinstance(teks, str) and (teks.startswith("[GAGAL]") or teks.startswith("[ERROR]")):
            # kembalikan detail agar frontend/ops bisa melihat alasannya
            return JSONResponse({"error": "Transkripsi gagal.", "detail": teks}, status_code=500)

        # Ringkas dengan LLaMA (kirim nama file sumber agar ringkasan bisa disimpan dengan nama yang cocok)
        source_fname = getattr(file, "filename", None)
        summary = ringkas_teks(teks, source_filename=source_fname)

        # Parsing hasil ringkasan
        dataInput = parse_ringkasan(summary)

        # Simpan form yang akan dipakai untuk injeksi di UI (disimpan sebagai JSON di uploads/)
        form_filename = isi_form(dataInput, source_filename=source_fname)

        # 5. Kembalikan hasil ke frontend
        return JSONResponse({
            "teks": teks,
            "summary": summary,
            "keluhan": dataInput.get("keluhan"),
            "riwayat": dataInput.get("riwayat"),
            "tekananDarah": dataInput.get("tekananDarah"),
            "assesmen": dataInput.get("assesmen"),
            "plan": dataInput.get("plan"),
            "form_file": form_filename
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)
