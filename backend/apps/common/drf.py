"""DRF drug names; collection officers enter each drug's current unit price."""
import json
from pathlib import Path

_source=json.loads((Path(__file__).parent/"data"/"drf_services.json").read_text())
CATALOGUE={
    **_source,
    "version": "2026-11-24.manual-prices.1",
    "manual_prices": True,
    "source_note": "Select drugs and enter their unit prices. Totals use the entered price and quantity; applicable patient discounts are calculated automatically.",
    "items": [{**{key:value for key,value in item.items() if key not in {"amount","source_rate"}},"kind":"editable"} for item in _source["items"]],
}
