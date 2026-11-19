import test from 'node:test';
import assert from 'node:assert/strict';
async function isolated(run){const oldFetch=globalThis.fetch,oldDocument=globalThis.document;globalThis.document={cookie:''};try{await run(await import(`../lib/api.js?test=${Math.random()}`));}finally{globalThis.fetch=oldFetch;if(oldDocument===undefined)delete globalThis.document;else globalThis.document=oldDocument;}}
test('user creation bootstraps CSRF without a readable cookie',()=>isolated(async({api})=>{const calls=[];globalThis.fetch=async(url,options)=>{calls.push({url,options});return Response.json(url.endsWith('/session/')?{csrf_token:'current-token'}:{id:42});};assert.equal((await api('users/',{method:'POST',body:'{}'})).id,42);assert.equal(calls[0].url,'/paypoint/api/v1/session/');assert.equal(calls[1].options.headers.get('X-CSRFToken'),'current-token');assert.equal(calls[1].options.credentials,'same-origin');}));
test('older login responses refresh rotated CSRF before creating users',()=>isolated(async({login,api})=>{let sessions=0;const tokens=[];globalThis.fetch=async(url,options)=>{if(url.endsWith('/session/'))return Response.json({csrf_token:++sessions===1?'before':'after'});tokens.push(options.headers.get('X-CSRFToken'));return Response.json({authenticated:true});};await login('synthetic','synthetic');await api('users/',{method:'POST',body:'{}'});assert.deepEqual(tokens,['before','after']);}));
test('explicit CSRF rejection refreshes then retries once',()=>isolated(async({getSession,api})=>{let sessions=0,writes=0;const tokens=[];globalThis.fetch=async(url,options)=>{if(url.endsWith('/session/'))return Response.json({csrf_token:++sessions===1?'old':'fresh'});tokens.push(options.headers.get('X-CSRFToken'));return ++writes===1?Response.json({detail:'CSRF Failed: CSRF token missing.'},{status:403}):Response.json({id:42});};await getSession();assert.equal((await api('users/',{method:'POST',body:'{}'})).id,42);assert.deepEqual(tokens,['old','fresh']);}));
test('permission errors are not retried and persistent CSRF failure stops',()=>isolated(async({api})=>{let writes=0,detail='Cannot create users.';globalThis.fetch=async(url)=>url.endsWith('/session/')?Response.json({csrf_token:'token'}):(writes++,Response.json({detail},{status:403}));await assert.rejects(api('users/',{method:'POST',body:'{}'}),/Cannot create/);assert.equal(writes,1);detail='CSRF Failed: token incorrect.';await assert.rejects(api('users/',{method:'POST',body:'{}'}),/CSRF Failed/);assert.equal(writes,3);}));

test('page-level session checks refresh CSRF after another tab rotates it',()=>isolated(async({api})=>{
  let token;
  globalThis.fetch=async(url,options)=>url.includes('/session/')?Response.json({csrf_token:'page-fresh-token'}):(token=options.headers.get('X-CSRFToken'),Response.json({id:42}));
  await api('session/?page=users-audit');
  await api('users/',{method:'POST',body:'{}'});
  assert.equal(token,'page-fresh-token');
}));
test('malformed browser cookie falls back to the server session token',()=>isolated(async({api})=>{
  globalThis.document.cookie='csrftoken=%E0%A4%A';
  const calls=[];
  globalThis.fetch=async(url,options)=>{calls.push(url);return url.endsWith('/session/')?Response.json({csrf_token:'server-token'}):(assert.equal(options.headers.get('X-CSRFToken'),'server-token'),Response.json({id:42}));};
  assert.equal((await api('users/',{method:'POST',body:'{}'})).id,42);
  assert.equal(calls.length,2);
}));
test('restricted browser cookie access still uses the same-origin session endpoint',()=>isolated(async({api})=>{
  globalThis.document={get cookie(){throw new Error('Storage access blocked');}};
  globalThis.fetch=async(url,options)=>url.endsWith('/session/')?Response.json({csrf_token:'server-token'}):(assert.equal(options.headers.get('X-CSRFToken'),'server-token'),Response.json({id:42}));
  assert.equal((await api('users/',{method:'POST',body:'{}'})).id,42);
}));
test('Firefox-style network failures are actionable and writes are never automatically repeated',()=>isolated(async({api,getSession})=>{
  globalThis.fetch=async()=>Response.json({csrf_token:'server-token'});await getSession();
  let attempts=0;globalThis.fetch=async()=>{attempts++;throw new TypeError('NetworkError when attempting to fetch resource.');};
  await assert.rejects(api('users/',{method:'POST',body:'{}'}),error=>error.message.includes('may have completed')&&error.method==='POST'&&error.path==='/paypoint/api/v1/users/');
  assert.equal(attempts,1);
  await assert.rejects(api('users/'),/Check your connection/);
}));
