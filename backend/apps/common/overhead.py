"""Hospital-approved Over-head prices. All submitted basket prices are rechecked here."""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from rest_framework import serializers

CATALOGUE=json.loads((Path(__file__).parent/'data'/'overhead_services.json').read_text())
ITEMS={item['code']:item for item in CATALOGUE['items']}
CENT=Decimal('0.01')

class OverheadSelection(serializers.Serializer):
    code=serializers.CharField(max_length=64)
    quantity=serializers.IntegerField(min_value=1,max_value=3650,default=1)
    unit_amount=serializers.DecimalField(max_digits=19,decimal_places=2,min_value=Decimal('0.01'),max_value=Decimal('1000000000'),required=False)


def price_basket(selections,patient_type):
    seen=set();lines=[];surcharge=False
    for selection in selections:
        code=selection['code'];item=ITEMS.get(code)
        if not item or code in seen:raise serializers.ValidationError({'overhead_items':'Select valid services only once; use quantity for repeats.'})
        seen.add(code);quantity=selection['quantity']
        if item['kind']=='percentage':
            if quantity!=1 or 'unit_amount' in selection:raise serializers.ValidationError('Surcharge is fixed at 10%.')
            surcharge=True;continue
        if item['kind']=='editable':
            if 'unit_amount' not in selection:raise serializers.ValidationError({'overhead_items':f"Enter a price for {item['name']}."})
            unit=selection['unit_amount']
        else:
            unit=Decimal(item['amount'])
            if 'unit_amount' in selection and selection['unit_amount']!=unit:raise serializers.ValidationError('Fixed Over-head prices cannot be changed.')
        amount=unit*quantity
        if item['kind']=='tiered':amount=unit+Decimal(item['subsequent_amount'])*(quantity-1)
        description=item['name']+(f" — {quantity} {item['unit']}{'s' if quantity!=1 else ''}" if quantity>1 or item['unit']!='unit' else '')
        if item['kind']=='tiered':description+=f" (first day {unit}; subsequent {item['subsequent_amount']})"
        lines.append({'code':code,'kind':item['kind'],'name':item['name'],'description':description,'quantity':quantity,'unit':item['unit'],'unit_amount':str(unit),'gross_amount':str(amount.quantize(CENT))})
    if not lines:raise serializers.ValidationError({'overhead_items':'Add at least one Over-head service.'})
    subtotal=sum((Decimal(row['gross_amount']) for row in lines),Decimal('0'))
    surcharge_amount=(subtotal*Decimal('0.10')).quantize(CENT,rounding=ROUND_HALF_UP) if surcharge else Decimal('0.00')
    if surcharge:lines.append({'code':'surcharge','name':'Surcharge 10%','description':'Surcharge — 10% of selected Over-head subtotal','quantity':1,'unit':'unit','unit_amount':str(surcharge_amount),'gross_amount':str(surcharge_amount)})
    base=subtotal+surcharge_amount
    if base<=0:raise serializers.ValidationError('No payment is due. A paid receipt requires a positive total.')
    if base>Decimal('99999999999999999.99'):raise serializers.ValidationError('The selected total is too large.')
    discount=(base*Decimal('0.10')).quantize(CENT,rounding=ROUND_HALF_UP) if patient_type!='regular' else Decimal('0.00')
    net=base-discount
    # Allocate net cents proportionally so line totals always equal the paid amount.
    base_cents=int(base*100);net_cents=int(net*100)
    numerators=[int(Decimal(row['gross_amount'])*100)*net_cents for row in lines]
    cents=[value//base_cents for value in numerators]
    remainder=net_cents-sum(cents)
    for index in sorted(range(len(lines)),key=lambda i:numerators[i]%base_cents,reverse=True)[:remainder]:cents[index]+=1
    for row,value in zip(lines,cents):row['net_amount']=str((Decimal(value)/100).quantize(CENT))
    return {'version':CATALOGUE['version'],'items':lines,'subtotal':str(subtotal.quantize(CENT)),'surcharge':str(surcharge_amount),'base_total':str(base),'discount_total':str(discount),'net_total':str(net)}
