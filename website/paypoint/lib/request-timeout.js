// Bound the entire operation, including response bodies and CSRF preparation.
export function withDeadline(run,{signal,timeoutMs=25000,method='GET'}={}){
  const controller=new AbortController();
  let timer,onAbort;
  const cancelled=new Promise((_,reject)=>{
    onAbort=()=>{controller.abort(signal?.reason);reject(signal?.reason||new DOMException('Request cancelled','AbortError'));};
    if(signal?.aborted){onAbort();return;}
    signal?.addEventListener('abort',onAbort,{once:true});
    timer=setTimeout(()=>{
      const error=new Error(['GET','HEAD','OPTIONS'].includes(method)?'The server is taking too long to respond. Please try again.':'The server did not respond in time. The action may have completed; check the records before submitting again.');
      error.name='RequestTimeoutError';error.method=method;controller.abort(error);reject(error);
    },timeoutMs);
  });
  return Promise.race([cancelled,Promise.resolve().then(()=>{if(controller.signal.aborted)throw controller.signal.reason;return run(controller.signal);})]).finally(()=>{clearTimeout(timer);signal?.removeEventListener('abort',onAbort);});
}
