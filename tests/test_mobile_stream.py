import cv2
import numpy as np
from mobile_client.camera_stream import FrameIngestionHandler


def test_frame_decode_success():
    handler = FrameIngestionHandler()
    # Create a synthetic 100x100 test frame
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, encoded = cv2.imencode(".jpg", dummy_img)
    raw_bytes = encoded.tobytes()

    frame, err = handler.decode_frame(raw_bytes)
    assert err is None
    assert frame is not None
    assert frame.shape == (100, 100, 3)


def test_frame_decode_corrupted():
    handler = FrameIngestionHandler()
    bad_bytes = b"not-a-valid-image-stream"
    frame, err = handler.decode_frame(bad_bytes)
    assert frame is None
    assert "Failed to decode" in err