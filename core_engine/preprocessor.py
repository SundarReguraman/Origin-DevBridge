import cv2
import numpy as np
import os
import sys


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Orders 4 points in top-left, top-right, bottom-right, bottom-left order.
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left has smallest sum
    rect[2] = pts[np.argmax(s)]  # bottom-right has largest sum

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right has smallest diff
    rect[3] = pts[np.argmax(diff)]  # bottom-left has largest diff
    return rect


def rectify_perspective(image: np.ndarray) -> np.ndarray:
    """
    Detects the largest 4-sided polygon (whiteboard/sheet) and performs a perspective transform.
    """
    orig = image.copy()
    h, w = image.shape[:2]

    # 1. Grayscale and smooth
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 2. Edge detection with dilation to close broken edges
    edged = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edged, kernel, iterations=1)

    # 3. Find contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    target_contour = None
    min_area = 0.15 * (h * w)  # Must cover at least 15% of the total frame

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:
            target_contour = approx
            break

    # If 4 corners were not found, warn the user
    if target_contour is None:
        print("[WARN] No clear 4-corner whiteboard/paper boundary detected.")
        print("       Ensure all 4 corners of the board/sheet are clearly visible inside the photo frame.")
        return orig

    print("[INFO] Whiteboard boundary detected. Applying perspective warp...")

    # 4. Warp perspective to flat rectangle
    pts = target_contour.reshape(4, 2)
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Calculate width & height of the new straightened image
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))

    return warped


def adaptive_binarize(image: np.ndarray) -> np.ndarray:
    """
    Converts straightened image to high-contrast black/white sketch.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Adaptive Gaussian thresholding removes uneven lighting / shadows
    binarized = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
    )
    return binarized


if __name__ == "__main__":
    # Check if an image path was passed as an argument
    if len(sys.argv) < 2:
        print("\n[!] Usage: python core_engine/preprocessor.py <path_to_image>")
        print("[!] Example: python core_engine/preprocessor.py test.jpg\n")
        sys.exit(1)

    input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print(f"\n[ERROR] File not found: '{input_path}'\n")
        sys.exit(1)

    print(f"\n[1/3] Reading image: {input_path}...")
    img = cv2.imread(input_path)

    if img is None:
        print(
            f"[ERROR] OpenCV could not decode '{input_path}'. Check if it's a valid image."
        )
        sys.exit(1)

    # 1. Perspective Transform / Straightening
    print("[2/3] Rectifying perspective...")
    rectified = rectify_perspective(img)

    # 2. Adaptive Binarization (Black/White high contrast)
    print("[3/3] Applying adaptive binarization...")
    final_output = adaptive_binarize(rectified)

    # Save output to disk
    output_filename = "preprocessed_output.png"
    cv2.imwrite(output_filename, final_output)
    print(f"\n[DONE] Successfully saved processed image to: {output_filename}\n")