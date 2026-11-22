const pending=new Map(),listeners=new Set();
let state={pending:0,label:''};
function publish(){
  const requests=[...pending.values()];
  state={pending:requests.length,label:requests.sort((a,b)=>b.priority-a.priority)[0]?.label||''};
  for(const listener of listeners)listener(state);
}
export const getRequestState=()=>state;
export function subscribeRequests(listener){listeners.add(listener);listener(state);return()=>listeners.delete(listener);}
export function beginRequest(label='Waiting for server response…',priority=0){
  const key=Symbol();pending.set(key,{label,priority});publish();
  return()=>{if(pending.delete(key))publish();};
}
