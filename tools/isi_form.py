import os
import time
import html
import re

TEMPLATE_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'templates', 'soap_global.html')

def _replace_textarea(html_text, element_id, new_text):
    """Replace inner text of a textarea with id=element_id."""
    esc = html.escape(new_text or '')
    pattern = re.compile(r'(<textarea\b[^>]*\bid="' + re.escape(element_id) + r'"[^>]*>)(.*?)(</textarea>)', re.DOTALL | re.IGNORECASE)

    def _repl(m):
        return m.group(1) + esc + m.group(3)

    return pattern.sub(_repl, html_text)


def _replace_input_value(html_text, element_id, new_value):
    """Set value attribute for an input (add one if missing).
    Handles inputs like <input ... id="..." ... />
    """
    esc = html.escape(new_value or '')
    pattern = re.compile(r'(<input\b[^>]*\bid="' + re.escape(element_id) + r'"[^>]*>)', re.IGNORECASE)

    def _repl(m):
        tag = m.group(1)
        if re.search(r'\bvalue=\"', tag, re.IGNORECASE) or re.search(r"\bvalue=\'", tag, re.IGNORECASE):
            # replace existing value
            tag2 = re.sub(r'value=("|\').*?(\1)', f'value="{esc}"', tag)
            return tag2
        else:
            # insert before the ending >
            # keep self-closing / if present
            if tag.endswith('/>'):
                return tag[:-2] + f' value="{esc}"/>'
            else:
                return tag[:-1] + f' value="{esc}">'

    return pattern.sub(_repl, html_text)


def isi_form(dataInput, source_filename=None, output_dir=None):
    """Save the filled form as JSON in the project `uploads/` folder.

    Returns the saved filename (basename) relative to uploads/.
    """
    tools_dir = os.path.dirname(__file__)
    project_dir = os.path.abspath(os.path.join(tools_dir, '..'))
    uploads_dir = output_dir or os.path.join(project_dir, 'uploads/parse')
    os.makedirs(uploads_dir, exist_ok=True)

    form = {
        "s-ku": dataInput.get("keluhan") or "",
        "s-rps": dataInput.get("riwayat") or "",
        "kultur": dataInput.get("sosial") or "",
        # "jw-selected": dataInput.get("kejiwaan") or "jw-lain",
        "o-tekanan": dataInput.get("tekananDarah") or "",
        "o-nadi": dataInput.get("nadi") or "",
        "o-suhu": dataInput.get("suhu") or "",
        "o-nafas": dataInput.get("frekuensiNafas") or "",
        "o-bb": dataInput.get("beratBadan") or "",
        "soap-a": dataInput.get("assesmen") or "",
        "soap-p": dataInput.get("plan") or ""
    }

    # Determine filename
    if source_filename:
        base = os.path.splitext(os.path.basename(source_filename))[0]
        fname = f"form-{base}.json"
    else:
        fname = f"form-{int(time.time()*1000)}-{secrets.token_hex(3)}.json"

    outpath = os.path.join(uploads_dir, fname)
    # avoid overwrite
    if os.path.exists(outpath):
        fname = f"{os.path.splitext(fname)[0]}-{int(time.time()*1000)}.json"
        outpath = os.path.join(uploads_dir, fname)

    try:
        import json as _json
        with open(outpath, 'w', encoding='utf-8') as of:
            _json.dump(form, of, ensure_ascii=False, indent=2)
        print(f"[INFO] Form disimpan ke: {outpath}")
        return fname
    except Exception as e:
        print("[WARN] Gagal menyimpan form ke uploads:", e)
        return None
