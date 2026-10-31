export const API_BASE = '/paypoint/api/v1/';
const describe = value => typeof value === 'string' ? value : Array.isArray(value) ? value.map(describe).join(' ') : value && typeof value === 'object' ? Object.entries(value).map(([key,item])=>`${key.replaceAll('_',' ')}: ${describe(item)}`).join(' ') : String(value??'');
let sessionCsrf='';
const csrf = () => sessionCsrf || decodeURIComponent(document.cookie.split(';').map(s=>s.trim()).find(s=>s.startsWith('csrftoken='))?.slice(10)||'');
export function apiPath(path) {
  if (/^[a-z][a-z\d+.-]*:/i.test(path) || path.startsWith('//')) throw new Error('Invalid API destination.');
  const url=new URL(path.replace(/^\//,''),'https://paypoint.invalid'+API_BASE);
  if(url.origin!=='https://paypoint.invalid'||!url.pathname.startsWith(API_BASE))throw new Error('Invalid API destination.');
  return url.pathname+url.search;
}
async function request(path,options={}) {
  const method=(options.method||'GET').toUpperCase(),headers=new Headers(options.headers);
  if(options.body && !(options.body instanceof FormData))headers.set('Content-Type','application/json');
  if(!['GET','HEAD','OPTIONS'].includes(method))headers.set('X-CSRFToken',csrf());
  const response=await fetch(apiPath(path),{...options,method,headers,credentials:'same-origin',cache:'no-store'});
  if(!response.ok){let body;try{body=await response.json();}catch{}
    const error=new Error([describe(body?.detail),describe(body?.errors||(body?.detail?null:body))].filter(Boolean).join(' ')||`Request failed (${response.status}).`);
    error.status=response.status;
    if(response.status===401||(response.status===403&&body?.detail==='Authentication credentials were not provided.'))window.dispatchEvent(new Event('paypoint-session-expired'));
    throw error;
  }
  return response;
}
export async function api(path,options={}) {const response=await request(path,options);return response.status===204?null:response.headers.get('content-type')?.includes('application/json')?response.json():null;}
export const getSession=async()=>{const session=await api('session/');sessionCsrf=session?.csrf_token||'';return session;};
export const login=async(username,password)=>{await getSession();const session=await api('session/login/',{method:'POST',body:JSON.stringify({username,password})});sessionCsrf=session?.csrf_token||'';return session;};
export const logout=()=>api('session/logout/',{method:'POST'});
export async function download(path,filename) {const response=await request(path),url=URL.createObjectURL(await response.blob()),anchor=document.createElement('a');anchor.href=url;anchor.download=filename;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
