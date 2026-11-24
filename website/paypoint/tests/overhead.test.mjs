import test from 'node:test';
import assert from 'node:assert/strict';
import {calculateOverhead} from '../lib/overhead.js';
const catalogue={"items": [{"group": "Medical certificate", "code": "cert_employment", "name": "Fit cert for employment", "kind": "fixed", "unit": "unit", "amount": "5000"}, {"group": "Medical report", "code": "report_local", "name": "Medical report \u2014 local", "kind": "fixed", "unit": "unit", "amount": "5000"}, {"group": "Medical report", "code": "report_staff", "name": "Excuse duty for staff", "kind": "fixed", "unit": "unit", "amount": "0"}, {"group": "Dressing room", "code": "dressing_major", "name": "Major dressing", "kind": "fixed", "unit": "unit", "amount": "2500"}, {"group": "General", "code": "card", "name": "Card", "kind": "fixed", "unit": "unit", "amount": "1000"}, {"group": "Operation fees", "code": "operation_minor", "name": "Operation fee \u2014 minor", "kind": "editable", "unit": "unit"}, {"group": "Admission fee", "code": "surcharge", "name": "Surcharge \u2014 10% of selected items", "kind": "percentage", "unit": "unit"}, {"group": "Admission fee", "code": "doctor_ae", "name": "Dr. Care A/E", "kind": "tiered", "unit": "day", "amount": "10000", "subsequent_amount": "5000"}, {"group": "Admission fee", "code": "nursing_ae", "name": "Nursing care A/E", "kind": "tiered", "unit": "day", "amount": "6000", "subsequent_amount": "3000"}, {"group": "Admission fee", "code": "dustbin", "name": "Dustbin", "kind": "fixed", "unit": "week", "amount": "300"}, {"group": "Admission fee", "code": "phototherapy", "name": "Phototherapy", "kind": "editable", "unit": "day"}]};
test('multiple Over-head items apply optional surcharge before patient discount',()=>{
 const result=calculateOverhead(catalogue,[{code:'cert_employment',quantity:1},{code:'report_local',quantity:1},{code:'dressing_major',quantity:1},{code:'surcharge',quantity:1}],'nhis');
 assert.equal(result.valid,true);assert.equal(result.subtotalCents,1250000);assert.equal(result.surchargeCents,125000);assert.equal(result.netCents,1237500);
});
test('A/E care uses one first day and subsequent rates for remaining days',()=>{
 const result=calculateOverhead(catalogue,[{code:'doctor_ae',quantity:3},{code:'nursing_ae',quantity:3},{code:'surcharge',quantity:1}],'imshia');
 assert.equal(result.subtotalCents,3200000);assert.equal(result.netCents,3168000);
});
test('editable prices, days, weeks and zero-price items keep exact cent totals',()=>{
 const result=calculateOverhead(catalogue,[{code:'operation_minor',quantity:3,unit_amount:'0.05'},{code:'phototherapy',quantity:2,unit_amount:'1000.25'},{code:'dustbin',quantity:2},{code:'report_staff',quantity:1}],'nhis');
 assert.equal(result.baseCents,260065);assert.equal(result.discountCents,26007);assert.equal(result.netCents,234058);
 assert.equal(result.rows.at(-1).amountCents,0);
});
test('invalid choices and incomplete editable prices cannot produce a payable basket',()=>{
 for(const rows of [[],[{code:'unknown',quantity:1}],[{code:'phototherapy',quantity:1}],[{code:'card',quantity:0}],[{code:'card',quantity:1},{code:'card',quantity:1}],[{code:'surcharge',quantity:1}]])assert.equal(calculateOverhead(catalogue,rows).valid,false);
});

test('DRF pharmacy baskets use entered prices, quantities and patient discounts without surcharge',()=>{
 const drf={label:'DRF pharmacy',items:[{code:'pharmacy_001',name:'Cap Amoxil 500mg',kind:'editable',unit:'unit'},{code:'pharmacy_322',name:'Sachet Floranorm',kind:'editable',unit:'unit'}]};
 const selected=[{code:'pharmacy_001',quantity:2,unit_amount:'100'},{code:'pharmacy_322',quantity:1,unit_amount:'1500'}];
 assert.equal(calculateOverhead(drf,selected).netCents,170000);
 for(const patientType of ['nhis','imshia']){const result=calculateOverhead(drf,selected,patientType);assert.equal(result.netCents,153000);assert.equal(result.surchargeCents,0);}
 assert.equal(calculateOverhead(drf,[{code:'surcharge',quantity:1}]).valid,false);
 assert.match(calculateOverhead(drf,[]).error,/DRF pharmacy/);
});

// Exercise the imported department catalogue rather than synthetic tariff copies.
test('R/F departments isolate services and reject source entries awaiting confirmation',async()=>{
 const {readFile}=await import('node:fs/promises');
 const source=JSON.parse(await readFile(new URL('./fixtures/rf-services.json',import.meta.url),'utf8'));
 const ophthalmology={...source,items:source.items.filter(i=>i.department==='ophthalmology')};
 assert.equal(calculateOverhead(ophthalmology,[{code:'rf_02_001',quantity:2},{code:'rf_02_002',quantity:1}],'nhis').netCents,2070000);
 assert.equal(calculateOverhead(ophthalmology,[{code:'rf_08_001',quantity:1}]).valid,false);
 for(const item of source.items.filter(i=>!i.available))assert.equal(calculateOverhead(source,[{code:item.code,quantity:1}]).valid,false);
 const emergency={...source,items:source.items.filter(i=>i.department==='accident_and_emergency')};
 assert.equal(calculateOverhead(emergency,[{code:'rf_06_009',quantity:3},{code:'rf_06_010',quantity:3}]).netCents,3200000);
});

test('DRF price entry is required and recalculates from the officer-entered price',()=>{
 const catalogue={label:'DRF pharmacy',manual_prices:true,items:[{code:'drug',name:'Drug',kind:'editable',unit:'unit'}]};
 for(const value of [undefined,'','0','-1','1.001'])assert.equal(calculateOverhead(catalogue,[{code:'drug',quantity:1,unit_amount:value}]).valid,false);
 assert.equal(calculateOverhead(catalogue,[{code:'drug',quantity:3,unit_amount:'250.50'}],'nhis').netCents,67635);
});
