"""
Origin DevBridge - OCR & Spatial Graph Pipeline
================================================
Identifies structural nodes (boxes/rectangles) from preprocessed masks
and extracts associated text to construct spatial graph primitives.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import cv2
import numpy as np
import pytesseract
import os
import shutil


@dataclass
class DiagramNode:
  id: str
  text: str
  bbox: Tuple[int, int, int, int]  # (x, y, w, h)
  centroid: Tuple[int, int]  # (cx, cy)
  shape: str = "rectangle"


class OCRPipeline:

  def __init__(self, tesseract_config: str = "--psm 6", tesseract_cmd: Optional[str] = None):
    self.tesseract_config = tesseract_config
    self.tesseract_cmd = self._resolve_tesseract_cmd(tesseract_cmd)
    if self.tesseract_cmd:
      pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

  def _resolve_tesseract_cmd(self, configured_cmd: Optional[str]) -> Optional[str]:
    candidates = []
    if configured_cmd:
      candidates.append(configured_cmd)

    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd:
      candidates.append(env_cmd)

    for candidate in candidates:
      expanded = os.path.expanduser(candidate)
      if os.path.isfile(expanded):
        return expanded
      raise ValueError(
          f"Tesseract executable not found at configured path: {candidate}"
      )

    discovered = shutil.which("tesseract")
    if discovered and os.path.isfile(discovered):
      return discovered

    return None

  def detect_boxes(
      self, binary_img: np.ndarray, min_area_ratio: float = 0.005
  ) -> List[Tuple[int, int, int, int]]:
    """Detects rectangular diagram nodes from the binarized image."""
    h, w = binary_img.shape[:2]
    total_area = h * w
    min_area = total_area * min_area_ratio

    # Invert binary image: strokes become white (255), background black (0)
    inv = (
        cv2.bitwise_not(binary_img)
        if binary_img.mean() > 127
        else binary_img.copy()
    )

    # Morphological closing to seal handwritten box gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(inv, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, hierarchy = cv2.findContours(
        closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    detected_boxes = []
    for c in contours:
      area = cv2.contourArea(c)
      if area < min_area or area > (0.85 * total_area):
        continue

      peri = cv2.arcLength(c, True)
      approx = cv2.approxPolyDP(c, 0.03 * peri, True)

      # Roughly rectangular polygon
      if 4 <= len(approx) <= 6:
        x, y, bw, bh = cv2.boundingRect(c)
        aspect_ratio = float(bw) / bh
        # Diagram nodes typically have reasonable aspect ratios (not hairline lines)
        if 0.25 <= aspect_ratio <= 5.0:
          detected_boxes.append((x, y, bw, bh))

    # Deduplicate overlapping / nested boxes (Non-Maximum Suppression-lite)
    filtered_boxes = self._filter_overlapping(detected_boxes)
    # Sort top-to-bottom, left-to-right
    filtered_boxes.sort(key=lambda b: (b[1] // 50, b[0]))
    return filtered_boxes

  def _compute_iou_and_containment(self, boxA, boxB):
        """
        Calculates Intersection-over-Union (IoU) and containment ratio.
        box format: (x, y, w, h)
        """
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

        inter_w = max(0, xB - xA)
        inter_h = max(0, yB - yA)
        inter_area = inter_w * inter_h

        if inter_area == 0:
            return 0.0, 0.0

        areaA = boxA[2] * boxA[3]
        areaB = boxB[2] * boxB[3]

        iou = inter_area / float(areaA + areaB - inter_area)
        # Check if one box is substantially inside another (nested stroke detection)
        min_area = min(areaA, areaB)
        containment = inter_area / float(min_area)

        return iou, containment

  def _filter_overlapping(self, boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Deduplicates nested or heavily overlapping bounding boxes.
        Prioritizes the larger outer boundary when nested strokes occur.
        """
        if not boxes:
            return []

        # Sort by area descending so outer boxes take precedence
        sorted_boxes = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)
        keep = []

        for current in sorted_boxes:
            suppress = False
            for preserved in keep:
                iou, containment = self._compute_iou_and_containment(current, preserved)
                # If boxes overlap by > 30% or one is > 65% contained inside the other, suppress it
                if iou > 0.30 or containment > 0.65:
                    suppress = True
                    break
            if not suppress:
                keep.append(current)

        return keep

  def extract_nodes(
      self, binary_img: np.ndarray, original_img: Optional[np.ndarray] = None
  ) -> List[DiagramNode]:
    """Extracts node bounding boxes and performs spatial OCR within each node."""
    boxes = self.detect_boxes(binary_img)
    target_img = original_img if original_img is not None else binary_img

    nodes: List[DiagramNode] = []
    for idx, (x, y, bw, bh) in enumerate(boxes, start=1):
      # Add small inner padding to avoid picking up the border box stroke
      pad_x = max(int(bw * 0.08), 2)
      pad_y = max(int(bh * 0.08), 2)
      crop = target_img[
          y + pad_y : y + bh - pad_y, x + pad_x : x + bw - pad_x
      ]

      if crop.size == 0:
        continue

      # OCR text extraction on the cropped content
      raw_text = pytesseract.image_to_string(crop, config=self.tesseract_config)
      clean_text = " ".join(raw_text.strip().split()) or f"Node_{idx}"

      cx = x + bw // 2
      cy = y + bh // 2

      nodes.append(
          DiagramNode(
              id=f"node_{idx}",
              text=clean_text,
              bbox=(x, y, bw, bh),
              centroid=(cx, cy),
          )
      )

    return nodes


# -------------------------------------------------------------
# CLI Verification Runner
# -------------------------------------------------------------
if __name__ == "__main__":
  import sys

  if len(sys.argv) < 2:
    print("\nUsage: python core_engine/ocr_pipeline.py <path_to_binary_image>")
    print("Example: python core_engine/ocr_pipeline.py preprocessed_output.png\n")
    sys.exit(1)

  img_path = sys.argv[1]
  img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

  if img is None:
    print(f"Error loading {img_path}")
    sys.exit(1)

  pipeline = OCRPipeline()
  detected_nodes = pipeline.extract_nodes(img)

  print(f"\n[SUCCESS] Detected {len(detected_nodes)} diagram nodes:\n")
  debug_canvas = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

  for n in detected_nodes:
    x, y, w, h = n.bbox
    print(f"  • ID: {n.id} | Text: '{n.text}' | Pos: {n.centroid}")
    # Draw green bounding box & label on preview
    cv2.rectangle(debug_canvas, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(
        debug_canvas,
        n.text[:15],
        (x, max(y - 8, 15)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        2,
    )

  cv2.imwrite("ocr_detected_nodes.png", debug_canvas)
  print(
      "\nSaved node boundary visualization to: core_engine/ocr_detected_nodes.png\n"
  )