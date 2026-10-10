"""License signature tests using a public fake-machine fixture, never a paid key."""
import sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desktop"))
from oyunopti_booster import validate_license
SAMPLE = "eyJkZXZpY2UiOiJBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQSIsImV4cGlyZXMiOiIyMDI3LTEwLTEwIiwibm9uY2UiOiIwZjYxYzVjNDEzNzUxM2ZkIiwib3JkZXIiOiJQVUJMSUMtVEVTVC1OT1QtU0FMRSIsInBsYW4iOiJwcm8iLCJ2ZXJzaW9uIjoxfQ.8_Z0-x-R03n2TXc1r1igBw9q-vWJPwe9bJ1b2jE4lUm6hylYyLXGdV2R4SYpm154sq8_WNJSprw7S1bMByz-Cw"
fake_machine="A"*32
assert validate_license(SAMPLE, machine=fake_machine, current=date(2026,10,10))["plan"]=="pro"
for token,device,now in [
    (SAMPLE,"B"*32,date(2026,10,10)),
    (SAMPLE,fake_machine,date(2028,1,1)),
    (SAMPLE+"t",fake_machine,date(2026,10,10)),
    ("bad",fake_machine,date(2026,10,10)),
]:
    try:
        validate_license(token, machine=device, current=now)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid/expired/device-mismatched license accepted")
print("License signature, device binding, expiry and tamper tests passed")
