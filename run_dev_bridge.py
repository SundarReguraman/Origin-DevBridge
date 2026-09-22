import sys
import os
import cv2

from core_engine.preprocessor import rectify_perspective, adaptive_binarize
from core_engine.ocr_pipeline import OCRPipeline
from core_engine.mermaid_compiler import MermaidCompiler

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_devbridge.py <image_path>")
        sys.exit(1)

    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
        sys.exit(1)

    print("\n🚀 [1/3] Preprocessing image (perspective rectification & binarization)...")
    raw = cv2.imread(img_path)
    if raw is None:
        print(f"Error: unable to decode image file '{img_path}'.")
        sys.exit(1)
    rectified = rectify_perspective(raw)
    binary = adaptive_binarize(rectified)
    cv2.imwrite("debug_preprocessed.png", binary)

    print("🔍 [2/3] Extracting diagram nodes & OCR text...")
    ocr = OCRPipeline()
    nodes = ocr.extract_nodes(binary)
    print(f"       Found {len(nodes)} nodes.")

    print("⚡ [3/3] Compiling to Mermaid.js AST...")
    compiler = MermaidCompiler(direction="LR")
    mermaid_code = compiler.compile(nodes)

    print("\n" + "="*40)
    print("       RESULTING MERMAID CODE")
    print("="*40)
    print(mermaid_code)
    print("="*40 + "\n")

    # Save to a markdown file
    with open("output_diagram.md", "w") as f:
        f.write(mermaid_code)
    print("Saved output to output_diagram.md\n")

if __name__ == "__main__":
    main()