"""
Origin DevBridge - Workstation IPC & Clipboard Bridge
======================================================
Injects sanitized Mermaid diagrams directly into the operating system clipboard
for instant pasting into IDEs, notes, or web platforms.
"""

from typing import Optional
import sys
import subprocess


class ClipboardDaemon:
    def __init__(self, fallback_to_native: bool = True):
        self.fallback_to_native = fallback_to_native

    def copy(self, text: str) -> bool:
        """
        Attempts to write text to the system clipboard.
        Tries pyperclip first; falls back to OS-native CLI utilities.
        """
        # Primary method: pyperclip
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception as e:
            if not self.fallback_to_native:
                print(f"[ERROR] Clipboard write failed: {e}")
                return False

        # Fallback 1: Windows native clip.exe
        if sys.platform.startswith("win"):
            try:
                subprocess.run("clip", input=text.encode("utf-16"), check=True)
                return True
            except Exception as e:
                print(f"[WARN] Windows clip.exe failed: {e}")

        # Fallback 2: macOS pbcopy
        elif sys.platform == "darwin":
            try:
                subprocess.run("pbcopy", input=text.encode("utf-8"), check=True)
                return True
            except Exception as e:
                print(f"[WARN] macOS pbcopy failed: {e}")

        # Fallback 3: Linux xclip / xsel
        elif sys.platform.startswith("linux"):
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    subprocess.run(cmd, input=text.encode("utf-8"), check=True)
                    return True
                except Exception:
                    continue

        return False

    def paste(self) -> Optional[str]:
        """Reads current content from clipboard for verification."""
        try:
            import pyperclip
            return pyperclip.paste()
        except Exception:
            return None


if __name__ == "__main__":
    bridge = ClipboardDaemon()
    sample_diagram = (
        "flowchart LR\n"
        "    Client --> Gateway\n"
        "    Gateway --> Database\n"
    )

    print("[TEST] Writing sample diagram to OS clipboard...")
    success = bridge.copy(sample_diagram)

    if success:
        print("[SUCCESS] Diagram loaded into system clipboard! Try pressing Ctrl+V anywhere.")
        read_back = bridge.paste()
        print(f"[VERIFY READBACK]:\n{read_back}")
    else:
        print("[FAIL] Could not inject to clipboard.")