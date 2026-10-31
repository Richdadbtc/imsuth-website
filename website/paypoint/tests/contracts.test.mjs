import test from 'node:test';
import assert from 'node:assert/strict';
import {apiPath} from '../lib/api.js';
import {backendOrigin,upstreamUrl,proxyApi} from '../lib/proxy.js';
import {screenFromSegments,screenHref,navigationSections} from '../lib/navigation.js';
import {readFile} from 'node:fs/promises';

test('frontend requests stay inside the same-origin Django API namespace',()=>{
  assert.equal(apiPath('patients/?page=2'),'/paypoint/api/v1/patients/?page=2');
  for(const bad of ['https://evil.invalid','//evil.invalid','../profile','%2e%2e/profile'])assert.throws(()=>apiPath(bad));
});
test('backend origin must be configured for production and never contains credentials',()=>{
  assert.equal(backendOrigin(undefined), 'http://127.0.0.1:8012');
  for(const bad of [undefined,'file:///etc/passwd','https://user:secret@host.invalid','https://host.invalid/path'])assert.throws(()=>backendOrigin(bad,true));
});
test('proxy paths cannot escape the configured backend API',()=>{
  assert.equal(upstreamUrl('http://backend:8000',['patients'],'?page=2'),'http://backend:8000/api/v1/patients/?page=2');
  for(const bad of [['..'],['patients/../../admin'],['https:']])assert.throws(()=>upstreamUrl('http://backend:8000',bad));
});
test('proxy preserves session cookies, CSRF, Origin, multipart content and status',async()=>{
  const request=new Request('https://staging-paypoint.imsuth.org/paypoint/api/v1/patients/',{method:'POST',headers:{cookie:'sessionid=synthetic','x-csrftoken':'synthetic-csrf',origin:'https://staging-paypoint.imsuth.org','content-type':'application/json','x-forwarded-proto':'http'},body:JSON.stringify({first_name:'Synthetic'})});
  let forwarded;
  const response=await proxyApi(request,['patients'],{origin:'http://backend:8000',fetcher:async(url,options)=>{forwarded={url,...options};return new Response('{"id":"synthetic"}',{status:201,headers:{'content-type':'application/json','set-cookie':'sessionid=new-synthetic; HttpOnly; Path=/paypoint/'}});}});
  assert.equal(response.status,201);assert.equal(forwarded.headers.get('cookie'),'sessionid=synthetic');assert.equal(forwarded.headers.get('host'),'backend:8000');assert.equal(forwarded.headers.get('origin'),'http://backend:8000');assert.equal(forwarded.headers.get('x-csrftoken'),'synthetic-csrf');assert.equal(forwarded.headers.get('x-forwarded-proto'),'https');assert.equal(forwarded.cache,'no-store');assert.match(response.headers.get('set-cookie'),/HttpOnly/);assert.equal(response.headers.get('cache-control'),'private, no-store');
});
test('proxy streams binary receipt/export responses without JSON conversion',async()=>{
  const data=new Uint8Array([37,80,68,70,0,255]);
  const response=await proxyApi(new Request('https://staff.invalid/paypoint/api/v1/receipts/1/print/'),['receipts','1','print'],{origin:'http://backend:8000',fetcher:async()=>new Response(data,{headers:{'content-type':'application/pdf','content-disposition':'attachment; filename=receipt.pdf'}})});
  assert.deepEqual(new Uint8Array(await response.arrayBuffer()),data);assert.equal(response.headers.get('content-type'),'application/pdf');
});
test('proxy rejects oversized uploads without contacting Django',async()=>{
  const request=new Request('https://staff.invalid/paypoint/api/v1/profile/photo/',{method:'POST',headers:{origin:'https://staff.invalid','content-length':String(7*1024*1024)},body:'synthetic'});
  const response=await proxyApi(request,['profile','photo'],{origin:'http://backend:8000',fetcher:()=>{throw Error('Must not send');}});
  assert.equal(response.status,413);
});
test('proxy failures are sanitized and external redirects are never followed',async()=>{
  const request=()=>new Request('https://staff.invalid/paypoint/api/v1/profile/');
  const options={origin:'http://backend:8000',fetcher:async()=>{throw Error('secret-password');}};
  const response=await proxyApi(request(),['profile'],options);assert.equal(response.status,502);assert.doesNotMatch(await response.text(),/secret-password/);
  const redirect=await proxyApi(request(),['profile'],{...options,fetcher:async()=>new Response(null,{status:302,headers:{location:'https://external.invalid'}})});assert.equal(redirect.status,502);
});
test('App Router keeps the original dashboard and index links compatible',()=>{
  assert.equal(screenFromSegments(),'dashboard');assert.equal(screenFromSegments(['index.html']),'dashboard');assert.equal(screenFromSegments(['admin-services']),'admin-services');assert.equal(screenHref('dashboard'),'/');assert.equal(screenHref('billing-create'),'/billing-create');
});
test('all navigation screens and legacy workflows have a retained controller',async()=>{
  const source=await readFile(new URL('../features/workspace.js',import.meta.url),'utf8');
  for(const {items} of navigationSections)for(const [route] of items)assert.match(source,new RegExp(`(?:["']${route}["']|\\b${route})\\s*[:,]`),route);
  assert.doesNotMatch(source,/await getSession|renderNavigation\(\);|window\.PAYPOINT_CONFIG|location\.hash/);
});

test('proxy validates the browser origin before routing to the API host',async()=>{
  let forwarded;
  const request=new Request('http://localhost:3001/paypoint/api/v1/session/login/',{method:'POST',headers:{host:'127.0.0.1:3001',origin:'http://127.0.0.1:3001'},body:'{}'});
  await proxyApi(request,['session','login'],{origin:'http://backend:8000',fetcher:async(url,options)=>{forwarded=options.headers;return new Response('{}');}});
  assert.equal(forwarded.get('host'),'backend:8000');assert.equal(forwarded.get('origin'),'http://backend:8000');
});

test('real HTTP transport routes the API host and preserves CSRF and individual cookies',async()=>{
  const {createServer}=await import('node:http');
  let incoming;
  const server=createServer((request,response)=>{incoming=request.headers;response.setHeader('Set-Cookie',['sessionid=synthetic; HttpOnly','csrftoken=synthetic; SameSite=Lax']);response.setHeader('Content-Type','application/json');response.end('{}');});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  try {
    const request=new Request('http://localhost:3001/paypoint/api/v1/session/login/',{method:'POST',headers:{host:'127.0.0.1:3001',origin:'http://127.0.0.1:3001','x-csrftoken':'synthetic'},body:'{}'});
    const response=await proxyApi(request,['session','login'],{origin:`http://127.0.0.1:${server.address().port}`});
    await response.text();
    assert.equal(incoming.host,`127.0.0.1:${server.address().port}`);assert.equal(incoming.origin,`http://127.0.0.1:${server.address().port}`);assert.equal(incoming['x-csrftoken'],'synthetic');assert.equal(incoming['content-length'],'2');assert.equal(incoming['transfer-encoding'],undefined);assert.equal(response.headers.getSetCookie().length,2);
  } finally {await new Promise(resolve=>server.close(resolve));}
});

test('compressed upstream responses keep their encoding for the browser',async()=>{
  const {gzipSync}=await import('node:zlib');
  const compressed=gzipSync('synthetic-export');
  const response=await proxyApi(new Request('https://staff.invalid/paypoint/api/v1/reports/revenue/'),['reports','revenue'],{origin:'http://backend:8000',fetcher:async()=>new Response(compressed,{headers:{'content-encoding':'gzip','content-type':'text/csv'}})});
  assert.equal(response.headers.get('content-encoding'),'gzip');assert.deepEqual(Buffer.from(await response.arrayBuffer()),compressed);
});

test('Vercel builds Next.js and redirects the domain root into PayPoint',async()=>{
  const config=JSON.parse(await readFile(new URL('../vercel.json',import.meta.url),'utf8'));
  assert.equal(config.framework,'nextjs');assert.equal(config.buildCommand,'npm run build:vercel');assert.equal(config.outputDirectory,'.next');
  assert.deepEqual(config.redirects,[{source:'/',destination:'/paypoint',permanent:false}]);
});
test('self-hosted and Vercel builds use the appropriate output adapters',async()=>{
  const {spawnSync}=await import('node:child_process');
  for(const [flag,expected] of [['1',null],['0','standalone']]){
    const result=spawnSync(process.execPath,['--input-type=module','-e',"import config from './next.config.mjs';console.log(JSON.stringify(config.output??null));"],{cwd:new URL('../',import.meta.url),encoding:'utf8',env:{...process.env,VERCEL:flag}});
    assert.equal(result.status,0,result.stderr);assert.equal(JSON.parse(result.stdout),expected);
  }
});

 test('proxy rejects cross-site writes before contacting the API',async()=>{
 for(const origin of ['https://evil.invalid',null]){
 const headers={host:'staff.invalid'};if(origin)headers.origin=origin;
 const response=await proxyApi(new Request('https://staff.invalid/paypoint/api/v1/session/login/',{method:'POST',headers,body:'{}'}),['session','login'],{origin:'https://api.imsuth.site',fetcher:()=>{throw Error('Must not contact API');}});
 assert.equal(response.status,403);
 }
});
 test('Vercel uses the approved production API origin',async()=>{
 const config=JSON.parse(await readFile(new URL('../vercel.json',import.meta.url),'utf8'));
 assert.equal(config.env.DJANGO_API_ORIGIN,'https://api.imsuth.site');
});

test('login uses session CSRF when the cookie path excludes the login page',async()=>{
 const previousFetch=globalThis.fetch,previousDocument=globalThis.document;
 const calls=[];globalThis.document={cookie:''};
 globalThis.fetch=async(url,options)=>{calls.push({url,options});return Response.json(url.endsWith('/session/')?{authenticated:false,csrf_token:'synthetic-session-csrf'}:{authenticated:true,csrf_token:'synthetic-rotated-csrf'});};
 try {const {login}=await import('../lib/api.js');await login('synthetic','synthetic');
 assert.equal(calls.length,2);assert.equal(calls[0].url,'/paypoint/api/v1/session/');
 assert.equal(calls[1].options.headers.get('X-CSRFToken'),'synthetic-session-csrf');
 }finally{globalThis.fetch=previousFetch;if(previousDocument===undefined)delete globalThis.document;else globalThis.document=previousDocument;}
});
