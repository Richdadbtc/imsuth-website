import {withDeadline} from './request-timeout.js';
import {beginRequest} from './request-state.js';
export const API_BASE = '/paypoint/api/v1/';
const describe = value => typeof value === 'string' ? value : Array.isArray(value) ? value.map(describe).join(' ') : value && typeof value === 'object' ? Object.entries(value).map(([key,item])=>`${key.replaceAll('_',' ')}: ${describe(item)}`).join(' ') : String(value??'');
let sessionCsrf='';
const csrf = () => {
  if(sessionCsrf)return sessionCsrf;
  try{return decodeURIComponent(document.cookie.split(';').map(s=>s.trim()).find(s=>s.startsWith('csrftoken='))?.slice(10)||'');}
  catch{return '';}
};
export function apiPath(path) {
  if (/^[a-z][a-z\d+.-]*:/i.test(path) || path.startsWith('//')) throw new Error('Invalid API destination.');
  const url=new URL(path.replace(/^\//,''),'https://paypoint.invalid'+API_BASE);
  if(url.origin!=='https://paypoint.invalid'||!url.pathname.startsWith(API_BASE))throw new Error('Invalid API destination.');
  return url.pathname+url.search;
}
async function request(path,options={},csrfRetried=false) {
  const method=(options.method||'GET').toUpperCase(),headers=new Headers(options.headers);
  if(options.body && !(options.body instanceof FormData))headers.set('Content-Type','application/json');
  const unsafe=!['GET','HEAD','OPTIONS'].includes(method);
  if(unsafe&&!csrf())await getSession({signal:options.signal});
  if(unsafe)headers.set('X-CSRFToken',csrf());
  let response;
  try{response=await fetch(apiPath(path),{...options,method,headers,credentials:'same-origin',cache:'no-store'});}
  catch(cause){
    if(cause.name==='AbortError'||options.signal?.aborted)throw cause;
    const error=new Error(unsafe?'The connection was interrupted. The action may have completed; check the records before submitting again.':'Unable to reach PayPoint. Check your connection and reload this page.');
    error.method=method;error.path=apiPath(path);throw error;
  }
  if(!response.ok){let body;try{body=await response.json();}catch{}
if(unsafe&&!csrfRetried&&response.status===403&&/^CSRF Failed:/i.test(body?.detail||'')){sessionCsrf='';await getSession({signal:options.signal});return request(path,options,true);}
        const error=new Error([describe(body?.detail),describe(body?.errors||(body?.detail?null:body))].filter(Boolean).join(' ')||`Request failed (${response.status}).`);
    error.status=response.status;error.method=method;error.path=apiPath(path);
    if(response.status===401||(response.status===403&&body?.detail==='Authentication credentials were not provided.'))window.dispatchEvent(new Event('paypoint-session-expired'));
    throw error;
  }
  return response;
}
export async function api(path,options={}) {
  const method=(options.method||'GET').toUpperCase(),writing=!['GET','HEAD','OPTIONS'].includes(method);
  const account=/^users\/(?:[0-9]+\/)?$/.test(path);
  const finish=beginRequest(account&&writing?(method==='POST'?'Creating account…':'Updating account…'):writing?'Saving changes…':'Waiting for server response…',writing?1:0);
  try{
  return await withDeadline(async signal=>{
  const response=await request(path,{...options,signal});
  let payload=null;
  if(response.status!==204){
    if(!response.headers.get('content-type')?.includes('application/json'))throw new Error('The server returned an unexpected response. Please reload the page and try again.');
    try{payload=await response.json();}catch(cause){if(signal.aborted)throw cause;throw new Error('The server response was incomplete. Please reload the page and try again.');}
  }
  // Page-level session checks also refresh the token after a login in another tab.
  if(/^session\/(?:\?|$)/.test(path)&&payload?.csrf_token)sessionCsrf=payload.csrf_token;
  return payload;
  },{signal:options.signal,method});
  }catch(error){reportError(error,options.signal);throw error;}finally{finish();}
}
export const getSession=async(options={})=>{const session=await api('session/',options);sessionCsrf=session?.csrf_token||'';return session;};
export const login=async(username,password)=>{await getSession();const session=await api('session/login/',{method:'POST',body:JSON.stringify({username,password})});sessionCsrf=session?.csrf_token||'';if(!sessionCsrf)await getSession();return session;};
export const logout=()=>api('session/logout/',{method:'POST'});
export async function download(path,filename) {const finish=beginRequest('Preparing download…');try{return await withDeadline(async signal=>{const response=await request(path,{signal}),url=URL.createObjectURL(await response.blob()),anchor=document.createElement('a');anchor.href=url;anchor.download=filename;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);},{timeoutMs:60000});}catch(error){reportError(error);throw error;}finally{finish();}}
function reportError(error,signal){
  if(signal?.aborted||error?.name==='AbortError'||typeof window==='undefined')return;
  if(error.reported)return;error.reported=true;
  window.dispatchEvent(new CustomEvent('paypoint-request-error',{detail:{message:error.message||'The request could not be completed. Please try again.',status:error.status}}));
}
