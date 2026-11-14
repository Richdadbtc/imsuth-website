import {API_BASE} from '../lib/api.js';

export function receiptPreviewPath(href,origin) {
  const url=new URL(href,origin);
  if(url.origin!==origin || !new RegExp(`^${API_BASE}receipts/[a-f0-9-]+/print/$`,'i').test(url.pathname)) return null;
  return url.pathname+url.search;
}

export function mountReceiptPreview(content,signal) {
  let active=null;
  const close=()=>{if(!active)return;active.controller.abort();active.dialog.close();active.dialog.remove();active.trigger?.focus();active=null;};
  signal.addEventListener('abort',close,{once:true});
  content.addEventListener('click',async event=>{
    const trigger=event.target.closest('a[href]');
    if(!trigger || event.button!==0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)return;
    const path=receiptPreviewPath(trigger.href,window.location.origin);
    if(!path)return;
    event.preventDefault();close();
    const controller=new AbortController(),dialog=document.createElement('dialog');
    dialog.className='receipt-preview-dialog';
    dialog.innerHTML='<header><div><h2 id="receipt-preview-title">Receipt preview</h2><p>Review the receipt before printing.</p></div><button type="button" data-close aria-label="Close receipt preview">Close</button></header><p role="status">Loading verified receipt…</p><iframe title="Official receipt preview" sandbox="allow-same-origin allow-modals" hidden></iframe><footer><button type="button" data-print disabled>Print receipt</button></footer>';
    dialog.setAttribute('aria-labelledby','receipt-preview-title');
    content.append(dialog);active={dialog,controller,trigger};
    const status=dialog.querySelector('[role=status]'),frame=dialog.querySelector('iframe'),print=dialog.querySelector('[data-print]');
    dialog.querySelector('[data-close]').onclick=close;
    dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
    print.onclick=()=>{if(!print.disabled){frame.contentWindow.focus();frame.contentWindow.print();}};
    dialog.showModal();
    try {
      const response=await fetch(path,{credentials:'same-origin',cache:'no-store',signal:controller.signal});
      if(!response.ok || !response.headers.get('content-type')?.includes('text/html'))throw new Error('Receipt unavailable. Check payment verification and your access, then try again.');
      const doc=new DOMParser().parseFromString(await response.text(),'text/html');
      // The authenticated receipt is passive HTML. Its inline styles use the page's CSP nonce.
      doc.querySelectorAll('script').forEach(node=>node.remove());
      const nonce=document.querySelector('script[nonce]')?.nonce;
      if(nonce)doc.querySelectorAll('style').forEach(node=>node.setAttribute('nonce',nonce));
      frame.addEventListener('load',async()=>{
        try {
          await Promise.all([...frame.contentDocument.images].map(img=>img.decode()));
          await frame.contentDocument.fonts.ready;
          if(controller.signal.aborted || !dialog.isConnected)return;
          status.textContent='Receipt ready. Review the details, then select Print receipt.';print.disabled=false;
        } catch {status.textContent='Receipt images could not load. Close the preview and try again.';}
      },{once:true});
      if(controller.signal.aborted || !dialog.isConnected)return;
      frame.hidden=false;frame.srcdoc='<!doctype html>'+doc.documentElement.outerHTML;
    } catch(error) {if(!controller.signal.aborted)status.textContent=error.message;}
  },{signal});
}
