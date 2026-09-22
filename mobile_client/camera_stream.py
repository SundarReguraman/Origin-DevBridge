"""
Origin DevBridge - Optical Frame Ingestion Handler
==================================================
Handles decoding and buffer validation of raw optical frames
transmitted by the mobile viewfinder client.
"""

from typing import Optional, Tuple
import cv2
import numpy as np


class FrameIngestionHandler:
    def __init__(self, max_payload_bytes: int = 15 * 1024 * 1024):
        self.max_payload_bytes = max_payload_bytes

    def decode_frame(self, raw_bytes: bytes) -> Tuple[Optional[np.ndarray], Optional[str]]:
        """
        Validates payload size and safely decodes raw JPEG/PNG bytes into an OpenCV matrix.
        Returns:
            (cv2_image, error_message)
        """
        if not raw_bytes:
            return None, "Empty payload received"

        if len(raw_bytes) > self.max_payload_bytes:
            return None, f"Payload exceeded limit ({len(raw_bytes)} > {self.max_payload_bytes})"

        # Convert bytes to numpy uint8 buffer
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return None, "Failed to decode image buffer. Invalid JPEG/PNG format"

        return frame, None