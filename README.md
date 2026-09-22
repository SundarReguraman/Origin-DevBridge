# Origin-DevBridge

From Snap to Screen, Origin DevBridge converts a photo of a whiteboard/paper architecture diagram into Mermaid flowchart output.

## Setup

1. Create and activate a virtual environment.
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

### Install Tesseract OCR binary (required)

`pytesseract` is a Python wrapper and requires the native `tesseract` executable.

- **macOS (Homebrew):** `brew install tesseract`
- **Ubuntu/Debian:** `sudo apt-get update && sudo apt-get install -y tesseract-ocr`
- **Windows:** install Tesseract OCR from the official installer and ensure `tesseract.exe` is on `PATH`.

If Tesseract is not on `PATH`, set an explicit path with `TESSERACT_CMD` before running:

- macOS/Linux: `export TESSERACT_CMD=/absolute/path/to/tesseract`
- Windows (PowerShell): `$env:TESSERACT_CMD='C:\\path\\to\\tesseract.exe'`

The OCR pipeline will use `TESSERACT_CMD` when provided, otherwise it will auto-detect `tesseract` from `PATH`.

## Run

```bash
python run_dev_bridge.py <image_path>
```
