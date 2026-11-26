import test from 'node:test';
import assert from 'node:assert/strict';
import {bindFormErrorModal} from '../features/request-feedback.js';
function fixture(){
 const fields=[{name:'email',labels:[{textContent:'Email Address *'}],willValidate:true,validity:{valid:false},validationMessage:'Please enter an email address.',focus(){this.focused=true;}},{name:'password',labels:[{textContent:'Initial password *'}],willValidate:true,validity:{valid:false},validationMessage:'Please fill out this field.',value:'never-display-this-password',focus(){}}];
 const form={isConnected:true,elements:fields,addEventListener(type,callback){this.listener=callback;},removeEventListener(){this.listener=null;}};
 return {form,fields};
}
test('native account validation shows one modal containing all field errors without values',async()=>{
 const {form,fields}=fixture(),messages=[];let prevented=0;
 const cleanup=bindFormErrorModal(form,message=>messages.push(message));
 form.listener({preventDefault(){prevented++;}});form.listener({preventDefault(){prevented++;}});
 await Promise.resolve();assert.equal(prevented,2);assert.equal(messages.length,1);
 assert.match(messages[0],/Email Address/);assert.match(messages[0],/Initial password/);assert.doesNotMatch(messages[0],/never-display/);assert.equal(fields[0].focused,true);cleanup();assert.equal(form.listener,null);
});
test('leaving the screen suppresses pending validation modals',async()=>{
 const {form}=fixture(),controller=new AbortController(),messages=[];
 bindFormErrorModal(form,message=>messages.push(message),{signal:controller.signal});
 form.listener({preventDefault(){}});controller.abort();await Promise.resolve();assert.deepEqual(messages,[]);
});
