let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let lastFormFile = null;

const recordBtn = document.getElementById("recordBtn");
const showTranscriptBtn = document.getElementById("showTranscriptBtn");
const modal = document.getElementById("transcriptModal");
const closeModal = document.getElementById("closeModal");
const resultText = document.getElementById("resultText");
const statusIndicator = document.getElementById("statusIndicator");

function setStatus(text, stateClass) {
    if (!statusIndicator) return;
    statusIndicator.textContent = text;
    statusIndicator.classList.remove('recording', 'sending', 'transkrip', 'ringkas', 'parse', 'done', 'idle');
    if (stateClass) statusIndicator.classList.add(stateClass);
}

// === Initial state ===
showTranscriptBtn.disabled = true;
setStatus('Status: Menunggu...', 'idle');

recordBtn.onclick = async () => {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.start();

            isRecording = true;
            recordBtn.textContent = "⏹️ Hentikan Rekaman dan Kirim";
            showTranscriptBtn.disabled = true;
            setStatus('Status: Merekam...', 'recording');
        } catch (err) {
            alert("Gagal mengakses mikrofon: " + err.message);
        }
    } else {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            isRecording = false;
            recordBtn.textContent = "🎙️ Mulai Rekam";
            setStatus('Status: Mengirim ke server...', 'sending');
        }
    }

    mediaRecorder.onstop = async () => {
        console.log("Rekaman selesai. Mengirim ke server...");

        if (!audioChunks.length) {
            setStatus('Status: Rekaman kosong.', 'idle');
            return;
        }

        const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "");
        const filename = `rekaman-${timestamp}.webm`;
        const blob = new Blob(audioChunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", blob, filename);

        try {
            setStatus('Status: Mengirim rekaman ke server...', 'transkrip');
            const response = await fetch("/transkrip", {
                method: "POST",
                body: formData
            });
            setStatus('Status: Hasil diterima, meringkas...', 'ringkas');

            const contentType = response.headers.get("content-type") || "";

            // Jika server masih memproses (bisa lama)
            setStatus('Status: Sedang mentranskrip...', 'transkrip');

            if (response.ok) {
                // === Jika hasil berupa JSON ===
                if (contentType.includes("application/json")) {
                    const data = await response.json();

                    // Jika whisper masih memproses atau hasil sementara
                    if (!data.teks || data.teks.toLowerCase().includes("whisper sedang memproses")) {
                        resultText.innerHTML = `<p>⏳ Whisper sedang memproses audio...</p>`;
                        setStatus('Status: Sedang mentranskrip...', 'transkrip');
                        return;
                    }

                    // === Jika hasil transkrip sudah tersedia ===
                    resultText.innerHTML = `<p>${data.teks}</p>`;
                    setStatus('Status: Meringkas data.', 'ringkas');
                    showTranscriptBtn.disabled = false;

                    // Simpan file form jika ada
                    if (data.form_file) lastFormFile = data.form_file;

                    // === Auto inject form langsung ===
                    if (lastFormFile) {
                        try {
                            setStatus('Status: Mengisi Form', 'parse');
                            const res = await fetch(`/uploads/parse/${encodeURIComponent(lastFormFile)}`);
                            if (res.ok) {
                                const formData = await res.json();
                                Object.entries(formData).forEach(([id, val]) => {
                                    const el = document.getElementById(id);
                                    if (el) {
                                        if (el.type === "radio" || el.type === "checkbox") {
                                            el.checked = !!val;
                                        } else {
                                            el.value = val;
                                        }
                                    }
                                });
                                console.log("✅ Form otomatis terisi berdasarkan hasil transkrip.");
                            } else {
                                console.warn("⚠️ Gagal memuat data form JSON.");
                            }
                        } catch (err) {
                            console.error("⚠️ Gagal fetch form JSON:", err);
                        }
                    }

                    alert("✅ Transkrip selesai & form otomatis terisi! Klik 📄 untuk melihat hasil transkrip.");
                    setStatus('Status: Selesai', 'done');
                } 
                // === Jika server mengirim teks (bukan JSON) ===
                else {
                    const teks = await response.text();
                    resultText.innerHTML = `<pre>${teks}</pre>`;

                    const lower = teks.toLowerCase();
                    // Be conservative: only treat explicit markers as errors so that
                    // progress/info logs (which may contain the word "error" in context)
                    // are not misinterpreted as a failure while Whisper is still running.
                    const indicatesError = lower.includes('[gagal]') || lower.includes('[error]') || lower.trim().startsWith('[gagal]') || lower.trim().startsWith('[error]');
                    const indicatesDone = lower.includes('transkrip selesai') || lower.includes('[result]') || lower.includes('hasil transkrip');

                    if (indicatesError) {
                        setStatus('Status: Gagal mentranskrip', 'recording');
                    } else if (indicatesDone) {
                        setStatus('Status: Selesai', 'done');
                    } else {
                        // Jika belum selesai tapi bukan error → biarkan status tetap transkrip
                        setStatus('Status: Sedang mentranskrip...', 'transkrip');
                    }
                }
            } else {
                // === Response non-OK (error 4xx/5xx) ===
                const teks = await response.text();
                resultText.innerHTML = `<pre style="color:red;">${teks}</pre>`;
                setStatus('Status: Gagal mentranskrip', 'recording');
            }
        } catch (err) {
            resultText.innerHTML = `<p style="color:red;">Gagal mengirim: ${err.message}</p>`;
            setStatus('Status: Gagal mengirim', 'recording');
        }
    }
};
// === Modal hanya untuk menampilkan hasil transkrip ===
showTranscriptBtn.onclick = () => {
    modal.style.display = "flex";
};

closeModal.onclick = () => modal.style.display = "none";
window.onclick = e => { if (e.target === modal) modal.style.display = "none"; };
