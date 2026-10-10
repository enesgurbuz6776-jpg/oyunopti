"""Check Pro's desktop/backend public key alignment and reject invalid tokens."""
import base64
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktop"))
from oyunopti_booster import PUBLIC_KEY_B64, validate_license

assert len(base64.b64decode(PUBLIC_KEY_B64)) == 32
server = (ROOT / "pro-backend" / "server.mjs").read_text(encoding="utf-8")
assert 'EXPECTED_PUBLIC_KEY = "' + PUBLIC_KEY_B64 + '"' in server

for invalid in ("", "bad", "a.b", "eyJmb28iOiJiYXIifQ.invalid"):
    try:
        validate_license(invalid, machine="A" * 32, current=date(2026, 10, 10))
    except ValueError:
        pass
    else:
        raise AssertionError("An invalid license was accepted")

print("PASS: desktop/server keys aligned; malformed licenses rejected")
