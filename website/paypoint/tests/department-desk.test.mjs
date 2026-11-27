import test from 'node:test';
import assert from 'node:assert/strict';
import {departmentDeskState} from '../lib/department-desk.js';

test('supervisor opens their assigned active department automatically', () => {
  const state=departmentDeskState([{id:'a',is_active:true},{id:'b',is_active:true}],{role:'department_supervisor',department:'b'});
  assert.equal(state.selected,'b');
  assert.deepEqual(state.departments.map(row=>row.id),['b']);
  assert.equal(state.locked,true);
});
test('missing or inactive assignments never fall back to another department', () => {
  const rows=[{id:'a',is_active:true},{id:'b',is_active:false}];
  for(const department of [null,'b','missing']) {
    const state=departmentDeskState(rows,{role:'department_supervisor',department});
    assert.equal(state.selected,'');
    assert.equal(state.departments.length,0);
    assert.match(state.notice,/administrator/);
  }
});
test('global users open the first active permitted department', () => {
  const state=departmentDeskState([{id:'a',is_active:false},{id:'b',is_active:true}],{role:'super_admin'});
  assert.equal(state.selected,'b');assert.equal(state.locked,false);
});
