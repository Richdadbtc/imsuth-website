import test from 'node:test';
import assert from 'node:assert/strict';
import {SLIP_PATTERN,referenceRule,isSlipChannel,normalizeSlipReference,formatTransferReference} from '../lib/slip-reference.js';
test('transfer uses first four and last five with an automatic slash',()=>{
  assert.equal(isSlipChannel('bank_transfer'),true);
  assert.equal(isSlipChannel('cash'),false);
  for(const value of ['09fgcy0w7','09fg/cy0w7','09fg2611042341124813\ncy0w7']) {
    assert.equal(formatTransferReference(value),'09FG/CY0W7');
  }
  assert.equal(formatTransferReference('000000000'),'0000/00000');
  assert.equal(formatTransferReference('09FG'),'09FG');
  assert.equal(formatTransferReference('09FGC'),'09FG/C');
  assert.equal(formatTransferReference('09FG/CY0W'),'09FG/CY0W');
  const pattern=new RegExp(`^${SLIP_PATTERN}$`);
  assert.equal(pattern.test(formatTransferReference('09FGCY0W7')),true);
  for(const value of ['09FG/CY0W','09FG/CY0W77','09FG//CY0W7','09FG/CY0W!']) assert.equal(pattern.test(value),false);
});

test('card uses the twelve-digit reference rather than transfer or six-digit codes',()=>{
 const card=new RegExp(`^${referenceRule('pos').pattern}$`);
 assert.equal(card.test('631313012611'),true);
 for(const value of ['012611','611231','09FG2611042341124813CY0W7','6313130126111','63131301261A']) assert.equal(card.test(value),false);
 assert.equal(new RegExp(`^${referenceRule('bank_transfer').pattern}$`).test('631313012611'),false);
});
