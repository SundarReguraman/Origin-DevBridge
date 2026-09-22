import sys
from bridge.clipboard_daemon import ClipboardDaemon


def test_clipboard_copy_and_paste():
    daemon = ClipboardDaemon()
    payload = "flowchart LR\n    NodeA --> NodeB"

    # Copy to clipboard
    success = daemon.copy(payload)
    assert success is True

    # Read back (if pyperclip is available in test environment)
    content = daemon.paste()
    if content is not None:
        assert "flowchart LR" in content
        assert "NodeA --> NodeB" in content