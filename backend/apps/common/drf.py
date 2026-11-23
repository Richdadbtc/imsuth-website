"""Pharmacy prices transcribed from the hospital-supplied list."""
import json
from pathlib import Path

CATALOGUE=json.loads((Path(__file__).parent/"data"/"drf_services.json").read_text())
