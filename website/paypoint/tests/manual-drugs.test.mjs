import test from 'node:test';
import assert from 'node:assert/strict';
import {calculateManualDrugs} from '../lib/manual-drugs.js';
test('typed drugs calculate quantities and discounts using entered unit prices',()=>{
 const rows=[{name:'Drug one',quantity:2,unit_amount:'1000.25'},{name:'Drug two',quantity:1,unit_amount:'100'}];
 assert.equal(calculateManualDrugs(rows).netCents,210050);
 assert.equal(calculateManualDrugs(rows,'nhis').netCents,189045);
});
test('blank, duplicate, overlong or incomplete drugs are not payable',()=>{
 for(const rows of [[],[{name:' ',quantity:1,unit_amount:'1'}],[{name:'X'.repeat(201),quantity:1,unit_amount:'1'}],[{name:'Drug',quantity:1,unit_amount:''}],[{name:'Drug',quantity:1,unit_amount:'0'}],[{name:'Drug',quantity:1,unit_amount:'1'},{name:'drug',quantity:1,unit_amount:'1'}]])assert.equal(calculateManualDrugs(rows).valid,false);
});
