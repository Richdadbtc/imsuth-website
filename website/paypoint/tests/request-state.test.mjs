import test from 'node:test';
import assert from 'node:assert/strict';
import {beginRequest,getRequestState,subscribeRequests} from '../lib/request-state.js';

test('overlapping requests keep loading active until all finish, and completion is idempotent',()=>{
  const seen=[],stop=subscribeRequests(state=>seen.push(state.pending));
  const one=beginRequest('Reading'),two=beginRequest('Creating account…',2);
  assert.deepEqual(getRequestState(),{pending:2,label:'Creating account…'});
  one();one();assert.equal(getRequestState().pending,1);
  two();assert.deepEqual(getRequestState(),{pending:0,label:''});
  stop();assert.deepEqual(seen,[0,1,2,1,0]);
});
test('account creation stays visible while its list refreshes and errors clear the state',async()=>{
  const {api}=await import('../lib/api.js');
  const previous=globalThis.fetch;
  const finish=beginRequest('Creating account…',2);
  globalThis.fetch=async()=>Response.json({detail:'Rejected'},{status:400});
  try{await assert.rejects(api('users/',{method:'GET'}),/Rejected/);assert.deepEqual(getRequestState(),{pending:1,label:'Creating account…'});}
  finally{finish();globalThis.fetch=previous;}
  assert.equal(getRequestState().pending,0);
});
test('unsubscribe stops request notifications',()=>{
  let changes=0;const stop=subscribeRequests(()=>changes++);stop();
  const finish=beginRequest();finish();assert.equal(changes,1);
});
