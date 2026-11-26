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

from rest_framework import serializers
from .overhead import OverheadSelection, price_basket

class DRFSelection(OverheadSelection):
    code=serializers.CharField(max_length=64,required=False)
    name=serializers.CharField(max_length=200,required=False,trim_whitespace=True)
    def validate(self,data):
        if bool(data.get('code'))==bool(data.get('name')):
            raise serializers.ValidationError('Enter a drug name or select an existing drug, not both.')
        if 'unit_amount' not in data:raise serializers.ValidationError('Enter the drug unit price.')
        if any(ord(c)<32 or ord(c)==127 for c in data.get('name','')):raise serializers.ValidationError('Enter a valid drug name.')
        return data

def price_drf(selections,patient_type):
    items=list(CATALOGUE['items']);priced=[];names=set()
    for index,selection in enumerate(selections):
        if 'name' in selection:
            name=selection['name'];normalized=name.casefold()
            if normalized in names:raise serializers.ValidationError({'drf_items':'Enter each drug once; use quantity for repeats.'})
            names.add(normalized);code=f'manual_drug_{index+1}'
            items.append({'code':code,'name':name,'kind':'editable','group':'Entered drugs','unit':'unit'})
            priced.append({**selection,'code':code})
        else:priced.append(selection)
    return price_basket(priced,patient_type,{**CATALOGUE,'items':items})
