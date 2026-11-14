import test from 'node:test';
import assert from 'node:assert/strict';
import {SLIP_PATTERN,referenceRule,isSlipChannel,normalizeSlipReference} from '../lib/slip-reference.js';
test('transfer requires complete normalized TRANS REF',()=>{
  assert.equal(isSlipChannel('pos'),true);
  assert.equal(isSlipChannel('bank_transfer'),true);
  assert.equal(isSlipChannel('cash'),false);
  const reference=normalizeSlipReference('09fg2611042341124813\ncy0w7');
  assert.equal(reference,'09FG2611042341124813CY0W7');
  const pattern=new RegExp(`^${SLIP_PATTERN}$`);
  assert.equal(pattern.test(reference),true);
  for(const invalid of ['123456','09FG2611042341124813CY0W','XXFG2611042341124813CY0W7']) assert.equal(pattern.test(invalid),false);
});

test('card uses the twelve-digit reference rather than transfer or six-digit codes',()=>{
 const card=new RegExp(`^${referenceRule('pos').pattern}$`);
 assert.equal(card.test('631313012611'),true);
 for(const value of ['012611','611231','09FG2611042341124813CY0W7','6313130126111','63131301261A']) assert.equal(card.test(value),false);
 assert.equal(new RegExp(`^${referenceRule('bank_transfer').pattern}$`).test('631313012611'),false);
});
