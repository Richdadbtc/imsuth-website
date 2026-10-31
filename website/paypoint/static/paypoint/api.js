/* Same-origin authenticated transport. No demonstration responses or local records. */
const API_BASE = new URL(window.PAYPOINT_CONFIG?.apiBase || '/paypoint/api/v1/', location.origin);
if (API_BASE.origin !== location.origin) throw new Error('PayPoint requires a same-origin API.');
if (!API_BASE.pathname.endsWith('/')) API_BASE.pathname += '/';
const cookie = name => document.cookie.split(';').map(value=>value.trim()).find(value=>value.startsWith(name+'='))?.slice(name.length+1) || '';
const describe = value => typeof value === 'string' ? value : Array.isArray(value) ? value.map(describe).join(' ') : value && typeof value === 'object' ? Object.entries(value).map(([key,item])=>`${key.replaceAll('_',' ')}: ${describe(item)}`).join(' ') : String(value??'');
const endpoint = path => {const url=new URL(path.replace(/^\//,''),API_BASE);if(url.origin!==API_BASE.origin||!url.pathname.startsWith(API_BASE.pathname))throw new Error('Invalid API destination.');return url;};
async function request(path,options={}) {
  const method=(options.method||'GET').toUpperCase(),headers=new Headers(options.headers||{});
  if(options.body&&!(options.body instanceof FormData))headers.set('Content-Type','application/json');
  if(!['GET','HEAD','OPTIONS'].includes(method))headers.set('X-CSRFToken',decodeURIComponent(cookie('csrftoken')));
  const response=await fetch(endpoint(path),{...options,method,headers,credentials:'same-origin',cache:'no-store'});
  if(!response.ok){let payload;try{payload=await response.json();}catch{}const error=new Error([describe(payload?.detail),describe(payload?.errors||(payload?.detail?null:payload))].filter(Boolean).join(' ')||`Request failed (${response.status}).`);error.status=response.status;error.payload=payload;if(response.status===401||(response.status===403&&payload?.detail==='Authentication credentials were not provided.'))window.dispatchEvent(new CustomEvent('paypoint-session-expired'));throw error;}
  return response;
}
export async function api(path,options={}) {const response=await request(path,options);return response.status===204?null:response.headers.get('content-type')?.includes('application/json')?response.json():null;}
export async function download(path,filename) {const response=await request(path),url=URL.createObjectURL(await response.blob()),link=document.createElement('a');link.href=url;link.download=filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export const getSession=()=>api('session/');
export const login=(username,password)=>api('session/login/',{method:'POST',body:JSON.stringify({username,password})});
export const logout=()=>api('session/logout/',{method:'POST'});
