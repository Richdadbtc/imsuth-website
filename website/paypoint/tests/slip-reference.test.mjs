import test from 'node:test';
import assert from 'node:assert/strict';
import {SLIP_PATTERN,isSlipChannel,normalizeSlipReference} from '../lib/slip-reference.js';
test('POS and transfer require complete normalized TRANS REF',()=>{
  assert.equal(isSlipChannel('pos'),true);
  assert.equal(isSlipChannel('bank_transfer'),true);
  assert.equal(isSlipChannel('cash'),false);
  const reference=normalizeSlipReference('09fg2611042341124813\ncy0w7');
  assert.equal(reference,'09FG2611042341124813CY0W7');
  const pattern=new RegExp(`^${SLIP_PATTERN}$`);
  assert.equal(pattern.test(reference),true);
  for(const invalid of ['123456','09FG2611042341124813CY0W','XXFG2611042341124813CY0W7']) assert.equal(pattern.test(invalid),false);
});
