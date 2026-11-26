import {subscribeRequests} from '../lib/request-state.js';

export const logoLoadingMarkup='<span class="imsuth-logo-orbit" aria-hidden="true"><img src="/paypoint/images/hospital%20logo.png" alt=""></span>';
export function mountRequestFeedback(host=document.body){
  const panel=document.createElement('div');panel.className='imsuth-request-feedback';panel.hidden=true;
  panel.setAttribute('role','status');panel.setAttribute('aria-live','polite');panel.setAttribute('aria-atomic','true');
  panel.innerHTML=logoLoadingMarkup+'<span data-request-label></span>';host.append(panel);
  let timer=null;
  const showError=event=>showRequestError(host,event.detail);
  window.addEventListener('paypoint-request-error',showError);
  const stop=subscribeRequests(state=>{
    if(!state.pending){clearTimeout(timer);timer=null;panel.hidden=true;return;}
    panel.querySelector('[data-request-label]').textContent=state.label;
    if(timer===null&&panel.hidden)timer=setTimeout(()=>{timer=null;panel.hidden=false;},0);
  });
  return()=>{stop();clearTimeout(timer);window.removeEventListener('paypoint-request-error',showError);host.querySelector('[data-request-error-dialog]')?.remove();panel.remove();};
}

export function showAccountCreated(host,account,{signal,refreshFailed=false}={}){
  const dialog=document.createElement('dialog');dialog.className='imsuth-account-created';
  dialog.setAttribute('aria-labelledby','account-created-title');dialog.setAttribute('aria-describedby','account-created-description');
  dialog.innerHTML='<img class="imsuth-success-logo" src="/paypoint/images/hospital%20logo.png" alt="IMSUTH"><span class="imsuth-success-check" aria-hidden="true">✓</span><h2 id="account-created-title">Account created</h2><p id="account-created-description"></p><p class="imsuth-success-username"></p><p data-refresh-warning hidden>The account was created, but the user list could not refresh. Refresh the page to see it; do not create the account again.</p><button type="button" class="button button-primary">Done</button>';
  dialog.querySelector('#account-created-description').textContent=`${account.full_name||[account.first_name,account.last_name].filter(Boolean).join(' ')||account.username}'s account has been created successfully.`;
  dialog.querySelector('.imsuth-success-username').textContent='Username: '+account.username;
  dialog.querySelector('[data-refresh-warning]').hidden=!refreshFailed;
  const previous=document.activeElement;
  const close=()=>{if(dialog.open)dialog.close();dialog.remove();signal?.removeEventListener('abort',close);if(previous?.isConnected)previous.focus();};
  dialog.querySelector('button').addEventListener('click',close);
  dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
  if(signal?.aborted)return;
  signal?.addEventListener('abort',close,{once:true});host.append(dialog);dialog.showModal();dialog.querySelector('button').focus();
}

export function showRequestError(host,{message,status}={}){
  let dialog=host.querySelector('[data-request-error-dialog]');
  if(dialog){dialog.querySelector('[data-error-message]').textContent=message;return;}
  dialog=document.createElement('dialog');dialog.className='imsuth-account-created imsuth-request-error';dialog.dataset.requestErrorDialog='';
  dialog.setAttribute('aria-labelledby','request-error-title');dialog.setAttribute('aria-describedby','request-error-description');
  dialog.innerHTML='<span class="imsuth-error-icon" aria-hidden="true">!</span><h2 id="request-error-title">Unable to complete request</h2><p id="request-error-description" data-error-message></p><button type="button" class="button button-primary">Close</button>';
  dialog.querySelector('[data-error-message]').textContent=message||'Please try again.';
  if(status===401)dialog.querySelector('h2').textContent='Please sign in again';
  const previous=document.activeElement;
  const close=()=>{if(dialog.open)dialog.close();dialog.remove();if(previous?.isConnected)previous.focus();};
  dialog.querySelector('button').addEventListener('click',close);
  dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
  host.append(dialog);dialog.showModal();dialog.querySelector('button').focus();
}
