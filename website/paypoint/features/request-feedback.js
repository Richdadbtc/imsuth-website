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

export function showRequestError(host,{message,status,title}={}){
  let dialog=host.querySelector('[data-request-error-dialog]');
  if(dialog){dialog.querySelector('[data-error-message]').textContent=message;dialog.querySelector('h2').textContent=status===401?'Please sign in again':title||'Unable to complete request';return;}
  dialog=document.createElement('dialog');dialog.className='imsuth-account-created imsuth-request-error';dialog.dataset.requestErrorDialog='';
  dialog.setAttribute('aria-labelledby','request-error-title');dialog.setAttribute('aria-describedby','request-error-description');
  dialog.innerHTML='<span class="imsuth-error-icon" aria-hidden="true">!</span><h2 id="request-error-title">Unable to complete request</h2><p id="request-error-description" data-error-message></p><button type="button" class="button button-primary">Close</button>';
  dialog.querySelector('[data-error-message]').textContent=message||'Please try again.';
  dialog.querySelector('h2').textContent=status===401?'Please sign in again':title||'Unable to complete request';
  const previous=document.activeElement;
  const close=()=>{if(dialog.open)dialog.close();dialog.remove();if(previous?.isConnected)previous.focus();};
  dialog.querySelector('button').addEventListener('click',close);
  dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
  host.append(dialog);dialog.showModal();dialog.querySelector('button').focus();
}

export function showPasswordReset(host,account,{reset,signal}={}){
  if(signal?.aborted||host.querySelector('[data-password-reset-dialog]'))return;
  const dialog=document.createElement('dialog');dialog.className='imsuth-account-created';dialog.dataset.passwordResetDialog='';
  dialog.setAttribute('aria-labelledby','password-reset-title');
  dialog.innerHTML='<h2 id="password-reset-title">Reset user password</h2><p data-reset-user></p><p>Set a new password for this user. Existing sessions will be signed out.</p><form><label>New password<input name="new_password" type="password" required maxlength="4096" autocomplete="new-password"></label><label>Confirm new password<input name="confirm_password" type="password" required maxlength="4096" autocomplete="new-password"></label><p data-reset-error role="alert"></p><button class="button button-primary" type="submit">Reset password</button><button type="button" data-reset-close>Cancel</button></form>';
  dialog.querySelector('[data-reset-user]').textContent=(account.full_name||account.username)+' ('+account.username+')';
  const previous=document.activeElement;let busy=false;
  const close=()=>{if(busy)return;if(dialog.open)dialog.close();dialog.remove();signal?.removeEventListener('abort',dispose);if(previous?.isConnected)previous.focus();};
  const dispose=()=>{busy=false;close();};
  signal?.addEventListener('abort',dispose,{once:true});
  dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
  dialog.querySelector('[data-reset-close]').onclick=close;
  const form=dialog.querySelector('form');
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(busy)return;
    const password=form.elements.new_password.value,confirmation=form.elements.confirm_password.value,error=dialog.querySelector('[data-reset-error]');
    if(password!==confirmation){error.textContent='Passwords do not match.';form.elements.confirm_password.focus();return;}
    error.textContent='';busy=true;form.setAttribute('aria-busy','true');form.querySelectorAll('input').forEach(input=>input.readOnly=true);
    const buttons=[...form.querySelectorAll('button')];buttons.forEach(button=>button.disabled=true);buttons[0].textContent='Resetting password…';
    try{
      await reset({new_password:password,confirm_password:confirmation});
      form.reset();if(!dialog.isConnected||signal?.aborted)return;
      dialog.innerHTML='<img class="imsuth-success-logo" src="/paypoint/images/hospital%20logo.png" alt="IMSUTH"><span class="imsuth-success-check" aria-hidden="true">✓</span><h2 id="password-reset-title">Password reset successfully</h2><p data-reset-success></p><button type="button" class="button button-primary">Done</button>';
      dialog.querySelector('[data-reset-success]').textContent=`The password for ${account.username} has been reset. Previous sessions have been signed out.`;
      dialog.querySelector('button').onclick=close;dialog.querySelector('button').focus();
    }catch(cause){if(dialog.isConnected)error.textContent=cause.message;}
    finally{busy=false;if(form.isConnected){form.removeAttribute('aria-busy');form.querySelectorAll('input').forEach(input=>input.readOnly=false);buttons.forEach(button=>button.disabled=false);buttons[0].textContent='Reset password';}}
  });
  host.append(dialog);dialog.showModal();form.elements.new_password.focus();
}

// Native form validation runs before submit; collect its errors in the same modal.
export function bindFormErrorModal(form,showError,{signal}={}){
  let queued=false;
  const invalid=event=>{
    event.preventDefault();if(queued)return;queued=true;
    queueMicrotask(()=>{
      queued=false;if(signal?.aborted||!form.isConnected)return;
      const fields=[...form.elements].filter(field=>field.willValidate&&!field.validity.valid);
      if(!fields.length)return;
      fields[0].focus();
      showError(fields.map(field=>{
        const label=field.labels?.[0];
        const name=label?.childNodes?[...label.childNodes].filter(node=>node.nodeType===3||node.nodeName==='SPAN').map(node=>node.textContent).join('').trim():label?.textContent?.trim();
        return `${name||field.name||'Field'}: ${field.validationMessage}`;
      }).join('\n'));
    });
  };
  form.addEventListener('invalid',invalid,{capture:true,signal});
  return()=>form.removeEventListener('invalid',invalid,true);
}
