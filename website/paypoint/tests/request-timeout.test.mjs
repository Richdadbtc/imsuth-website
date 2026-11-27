import test from 'node:test';
import assert from 'node:assert/strict';
import {withDeadline} from '../lib/request-timeout.js';
import {getRequestState} from '../lib/request-state.js';

test('stalled operations time out even when transport ignores cancellation',async()=>{
 let signal;
 await assert.rejects(withDeadline(value=>{signal=value;return new Promise(()=>{});},{timeoutMs:10}),error=>error.name==='RequestTimeoutError'&&/too long/.test(error.message));
 assert.equal(signal.aborted,true);
});
test('writes time out with an uncertain-outcome message and execute only once',async()=>{
 let attempts=0;
 await assert.rejects(withDeadline(()=>{attempts++;return new Promise(()=>{});},{timeoutMs:10,method:'POST'}),/may have completed/);
 assert.equal(attempts,1);
});
test('navigation cancellation propagates and successful operations clean up',async()=>{
 const controller=new AbortController();
 const task=withDeadline(()=>new Promise(()=>{}),{signal:controller.signal,timeoutMs:1000});controller.abort();
 await assert.rejects(task,error=>error.name==='AbortError');
 assert.equal(await withDeadline(async()=>42,{timeoutMs:10}),42);
});
test('API body timeout clears loading and reports one error; navigation cancellation stays quiet',async t=>{
 const previous={fetch:globalThis.fetch,window:globalThis.window};
 const errors=[];globalThis.window=new EventTarget();window.addEventListener('paypoint-request-error',event=>errors.push(event.detail));
 const {api}=await import('../lib/api.js?deadline-test');
 t.mock.timers.enable({apis:['setTimeout']});
 try{
   globalThis.fetch=async()=>({ok:true,status:200,headers:new Headers({'content-type':'application/json'}),json:()=>new Promise(()=>{})});
   const pending=api('slow/');const rejected=assert.rejects(pending,/too long/);
   await new Promise(resolve=>setImmediate(resolve));t.mock.timers.tick(25000);await rejected;
   assert.equal(getRequestState().pending,0);assert.equal(errors.length,1);
   const controller=new AbortController(),cancelled=api('cancel/',{signal:controller.signal});const cancelledCheck=assert.rejects(cancelled,error=>error.name==='AbortError');controller.abort();await cancelledCheck;
   assert.equal(getRequestState().pending,0);assert.equal(errors.length,1);
 }finally{t.mock.timers.reset();globalThis.fetch=previous.fetch;if(previous.window===undefined)delete globalThis.window;else globalThis.window=previous.window;}
});

test('invalid server replies become readable errors and release loading',async()=>{
 const previous=globalThis.fetch;
 const {api}=await import('../lib/api.js?invalid-response');
 try{
   globalThis.fetch=async()=>new Response('<html>Gateway error</html>',{headers:{'content-type':'text/html'}});
   await assert.rejects(api('bad/'),/unexpected response/);
   assert.equal(getRequestState().pending,0);
   globalThis.fetch=async()=>new Response('{',{headers:{'content-type':'application/json'}});
   await assert.rejects(api('bad/'),/incomplete/);
   assert.equal(getRequestState().pending,0);
 }finally{globalThis.fetch=previous;}
});

test('503 gateway replies give an actionable message and release loading without retrying',async()=>{
 const previous=globalThis.fetch;let attempts=0;
 const {api}=await import('../lib/api.js?gateway-503');
 try{
   globalThis.fetch=async()=>{attempts++;return new Response('Service Unavailable',{status:503,headers:{'content-type':'text/html'}});};
   await assert.rejects(api('audit-logs/?page=1'),error=>error.status===503&&/temporarily busy or unavailable/.test(error.message));
   assert.equal(attempts,1);assert.equal(getRequestState().pending,0);
 }finally{globalThis.fetch=previous;}
});
