"""Smoke test the Windows Tk application without starting real game monitoring."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desktop"))
from oyunopti_booster import App

app = App()
try:
    app.withdraw()  # prevent showing windows during automated build
    for page in ("Genel Bakış", "FPS Ölçümü", "OyunOpti Pro", "Pro Optimizasyon", "Canlı FPS Pro", "Geri Al", "Hakkında"):
        app.show(page)
        app.update()
    # Let the recurring FPS polling timer fire at least once.
    deadline = time.monotonic() + 1.1
    while time.monotonic() < deadline:
        app.update()
        time.sleep(0.05)
finally:
    app.destroy()
print("OyunOpti Tk GUI startup, navigation and FPS polling smoke test passed")
