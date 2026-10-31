'use client';
import {useEffect,useRef} from 'react';
import {mountWorkspace} from '../features/workspace.js';

/** React owns the route; the complete financial screens own only this isolated node. */
export default function Workspace({screen,user,filter,navigate,onSignedOut,onProfileSaved,onUnreadCount}) {
  const host=useRef(null),controller=useRef(null),callbacks=useRef({navigate,onSignedOut,onProfileSaved,onUnreadCount});
  callbacks.current={navigate,onSignedOut,onProfileSaved,onUnreadCount};
  useEffect(()=>{
    const content=document.createElement('div');content.className='page-shell';content.setAttribute('aria-live','polite');host.current.append(content);
    const onNavigate=event=>callbacks.current.navigate(event.detail);
    content.addEventListener('paypoint-navigate',onNavigate);
    const runtime=mountWorkspace(content,{user,navigate:(...args)=>callbacks.current.navigate(...args),onSignedOut:()=>callbacks.current.onSignedOut(),onProfileSaved:values=>callbacks.current.onProfileSaved(values),onUnreadCount:count=>callbacks.current.onUnreadCount(count)});
    controller.current=runtime;runtime.render(screen);
    return()=>{content.removeEventListener('paypoint-navigate',onNavigate);runtime.dispose();controller.current=null;};
    // A fresh screen scope prevents stale async requests from overwriting another route.
    // User profile callbacks update the parent without recreating an active financial form.
  },[screen,user.id]);
  useEffect(()=>{controller.current?.filter(filter);},[filter]);
  return <main id="main" ref={host} className="next-screen-host"/>;
}
