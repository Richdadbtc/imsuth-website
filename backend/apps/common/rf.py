"""Department-specific R/F catalogue from the supplied hospital document."""
import json
from pathlib import Path
CATALOGUE=json.loads((Path(__file__).parent/"data"/"rf_services.json").read_text())

def department_catalogue(code):
    department=next((d for d in CATALOGUE["departments"] if d["code"]==code),None)
    if not department:return None
    return {**CATALOGUE,"label":"R/F — "+department["name"],"department":department,"items":[i for i in CATALOGUE["items"] if i["department"]==code]}
