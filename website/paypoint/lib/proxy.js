import {request as httpRequest} from 'node:http';
import {request as httpsRequest} from 'node:https';
import {Readable} from 'node:stream';

// Stream responses and preserve individual cookies through the server-side proxy.
export function nodeTransport(url,options) {
  return new Promise((resolve,reject)=>{
    const parsed=new URL(url),send=parsed.protocol==='https:'?httpsRequest:httpRequest;
    const headersOut=Object.fromEntries(options.headers);
    if(!['GET','HEAD'].includes(options.method))headersOut['Content-Length']=String(options.body?.byteLength??0);
    const upstream=send(parsed,{method:options.method,headers:headersOut,signal:options.signal},incoming=>{
      const headers=new Headers();
      for(let i=0;i<incoming.rawHeaders.length;i+=2)headers.append(incoming.rawHeaders[i],incoming.rawHeaders[i+1]);
      const status=incoming.statusCode;
      const empty=options.method==='HEAD'||[204,304].includes(status);
      if(empty)incoming.resume();
      resolve(new Response(empty?null:Readable.toWeb(incoming),{status,headers}));
    });
    upstream.on('error',reject);
    if(options.body)upstream.write(options.body);
    upstream.end();
  });
}

const HOP_HEADERS=new Set(['connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','upgrade','content-length']);
export function backendOrigin(value,production=false) {
  if(!value && production)throw new Error('DJANGO_API_ORIGIN must be configured for deployment.');
  const url=new URL(value||'http://127.0.0.1:8012');
  if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.search||url.hash||url.pathname!=='/')throw new Error('Use a credential-free Django HTTP(S) origin.');
  return url.origin;
}
export function upstreamUrl(origin,segments,search='') {
  if(!segments?.length||segments.some(s=>!s||s==='.'||s==='..'||!/^[A-Za-z0-9_@.+~-]+$/.test(s)))throw new Error('Invalid API path.');
  return `${origin}/api/v1/${segments.map(encodeURIComponent).join('/')}/${search}`;
}
export async function proxyApi(request,segments,{origin,fetcher=nodeTransport}={}) {
  let target;
  try{target=upstreamUrl(origin,segments,new URL(request.url).search);}catch{return Response.json({detail:'Invalid API path.'},{status:400});}
  const headers=new Headers();
  // Do not forward arbitrary client proxy headers, server credentials or a different origin.
  for(const name of ['accept','content-type','cookie','x-csrftoken','idempotency-key','origin','referer']){
    const value=request.headers.get(name);if(value)headers.set(name,value);
  }
  const incoming=new URL(request.url);
  const browserHost=request.headers.get('host')||incoming.host;
  const browserOrigin=`${incoming.protocol}//${browserHost}`;
  const suppliedOrigin=request.headers.get('origin');
  if(!['GET','HEAD','OPTIONS'].includes(request.method)&&suppliedOrigin!==browserOrigin)
    return Response.json({detail:'Request origin is not allowed.'},{status:403});
  // The browser talks only to this same-origin BFF. After validating its origin,
  // route the request to the API virtual host and keep Django CSRF token checks.
  headers.set('Host',new URL(origin).host);
  if(suppliedOrigin)headers.set('Origin',origin);
  if(request.headers.get('referer'))headers.set('Referer',`${origin}/`);
  headers.set('X-Forwarded-Proto',incoming.protocol.slice(0,-1));
  headers.set('Accept-Encoding','identity');
  let body;
  if(!['GET','HEAD'].includes(request.method)){
    const maximum=6*1024*1024;
    if(Number(request.headers.get('content-length'))>maximum)return Response.json({detail:'Upload exceeds 6MB.'},{status:413});
    const reader=request.body?.getReader(),chunks=[];let bytes=0;
    if(reader)while(true){const {done,value}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>maximum){await reader.cancel();return Response.json({detail:'Upload exceeds 6MB.'},{status:413});}chunks.push(value);}
    body=chunks.length?Buffer.concat(chunks):undefined;
  }
  try {
    const upstream=await fetcher(target,{method:request.method,headers,body,cache:'no-store',redirect:'manual',signal:AbortSignal.any([request.signal,AbortSignal.timeout(30000)])});
    const outgoing=new Headers();
    upstream.headers.forEach((value,key)=>{if(!HOP_HEADERS.has(key.toLowerCase())&&!['set-cookie','location'].includes(key.toLowerCase()))outgoing.set(key,value);});
    for(const cookie of upstream.headers.getSetCookie())outgoing.append('Set-Cookie',cookie);
    const location=upstream.headers.get('location');
    if(location){const destination=new URL(location,target);if(destination.origin!==new URL(origin).origin)return Response.json({detail:'Unexpected upstream redirect.'},{status:502});outgoing.set('Location',destination.pathname.replace(/^\/api\/v1\//,'/paypoint/api/v1/')+destination.search);}
    outgoing.set('Cache-Control','private, no-store');
    return new Response(['HEAD'].includes(request.method)||[204,304].includes(upstream.status)?null:upstream.body,{status:upstream.status,headers:outgoing});
  }catch{return Response.json({detail:'The PayPoint API is currently unavailable. Please try again.'},{status:502,headers:{'Cache-Control':'private, no-store'}});}
}
