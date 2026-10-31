import {download} from '../lib/api.js';

export async function mountHospitalCatalogueSetup(content,{api,user,escapeHtml:esc}) {
  content.innerHTML=`<section class="catalogue-setup"><h1>Hospital Catalogue Setup</h1><p>Proposed, unverified department and category placeholders. Imports stay inactive and never create billable services or prices.</p><div class="finance-card"><h2>Preview source</h2><label>Optional validated CSV<input type="file" accept=".csv,text/csv" data-catalogue-file></label><p>Template columns: kind, code, name, department_code, parent_code. Maximum 500 entries / 512KB.</p><div class="catalogue-buttons"><button class="pending-outline" data-catalogue-master>Use proposed master catalogue</button><button class="pending-outline" data-catalogue-preview>Refresh preview</button><button class="pending-outline" data-catalogue-export>Export CSV template</button></div></div><p role="status" data-catalogue-message></p><section class="finance-card"><h2>Compare and select placeholders</h2><div data-catalogue-summary></div><div class="catalogue-buttons"><button class="pending-outline" data-catalogue-select>Select new entries</button><button class="pending-outline" data-catalogue-inactive>Select inactive entries</button><button class="pending-outline" data-catalogue-clear>Clear selection</button></div><div data-catalogue-rows></div><label>Import / activation request reason<input data-catalogue-reason maxlength="255" minlength="5" placeholder="Hospital review or approval reference and reason"></label><label class="catalogue-confirm"><input type="checkbox" data-catalogue-confirm> I confirm import of the selected inactive placeholders only.</label><div class="catalogue-buttons"><button class="pending-verify" data-catalogue-import>Import selected as inactive</button><button class="pending-outline" data-catalogue-request>Request activation review</button></div><p>Activation is separate from importing. A different active Super Administrator must review activation requests; departments and parent categories must be approved before their children.</p></section><section class="finance-card"><h2>Activation approvals</h2><p role="status" data-catalogue-review-status></p><button class="pending-outline" data-catalogue-select-approvals>Select all eligible requests</button><label>Decision reason<input data-catalogue-decision-reason maxlength="255" minlength="5" placeholder="Review findings and hospital approval reference"></label><div class="catalogue-buttons"><button class="pending-outline" data-catalogue-approve>Approve selected requests</button><button class="pending-outline" data-catalogue-reject>Reject selected requests</button></div><div data-catalogue-approvals></div></section><section class="finance-card"><h2>Import and activation audit history</h2><div data-catalogue-history></div></section></section>`;
  const root=content.querySelector('.catalogue-setup'),message=text=>root.querySelector('[data-catalogue-message]').textContent=text;
  let csv=null,report=null,selected=new Set(),generation=0,busy=false,approvalRows=[];
  const send=(operation,body)=>api('catalogue-setup/'+operation+'/',{method:'POST',body:JSON.stringify(body)});
  const reason=()=>root.querySelector('[data-catalogue-reason]').value.trim();
  const render=()=>{
    if(!report)return;
    root.querySelector('[data-catalogue-summary]').textContent=`${report.version} · ${report.summary.new} new · ${report.summary.existing} existing · ${report.summary.conflict} conflicting · ${report.summary.skipped} skipped. ${selected.size} selected. Existing codes, names and statuses are preserved.`;
    root.querySelector('[data-catalogue-rows]').innerHTML=`<div class="table-wrap"><table class="data-table finance-data-table"><thead><tr><th>Select</th><th>Kind / scope</th><th>Proposed code</th><th>Name</th><th>Comparison</th><th>Current state</th><th>Details</th></tr></thead><tbody>${report.rows.map(r=>`<tr><td><input type="checkbox" aria-label="Select ${esc(r.name)} (${esc(r.kind)})" data-catalogue-key="${esc(r.key)}" ${selected.has(r.key)?'checked':''} ${r.comparison_status==='conflict'?'disabled':''}></td><td>${esc(r.kind)}${r.department_code?' / '+esc(r.department_code):''}</td><td>${esc(r.code)}</td><td>${esc(r.name)}</td><td>${esc(r.comparison_status)}</td><td>${r.id?(r.is_active?'Active':'Inactive'):'Proposed inactive'}</td><td>${esc(r.note)}${r.actual_code!==r.code?' Existing code: '+esc(r.actual_code):''}</td></tr>`).join('')}</tbody></table></div>${report.existing_duplicates.length?'<p class="alert alert-error">Existing normalized code/name duplicates must be reconciled before importing. No records have been changed.</p>':''}<details><summary>Legacy service category labels (${report.legacy_service_categories.length})</summary><p>Existing service labels are retained and are not converted into billable services or silently reassigned.</p></details>`;
  };
  const preview=async(reset=false)=>{
    const version=++generation;message('Comparing proposed placeholders with existing catalogue…');
    const data=csv===null?await api('catalogue-setup/'):await send('preview',{csv});
    if(version!==generation||!root.isConnected)return;
    report=data;
    if(reset)selected=new Set();
    selected=new Set([...selected].filter(k=>report.rows.some(r=>r.key===k&&r.comparison_status!=='conflict')));
    root.querySelector('[data-catalogue-confirm]').checked=false;render();message('Preview only. No database records changed.');
  };
  const reviewState=()=>{
    const count=root.querySelectorAll('[data-catalogue-approval]:checked:not(:disabled)').length;
    const reasonLength=root.querySelector('[data-catalogue-decision-reason]').value.trim().length;
    const eligible=approvalRows.filter(a=>a.can_decide).length;
    const own=approvalRows.filter(a=>a.status==='pending'&&!a.can_decide).length;
    root.querySelector('[data-catalogue-review-status]').textContent=eligible?`${eligible} requests available for your review; ${count} selected. Enter a decision reason of at least 5 characters to approve or reject.`:own?`${own} pending requests were submitted by this account. Sign in as a different Super Administrator to approve them. You cannot review your own requests.`:'No pending requests available for your review. Import placeholders, select inactive entries, and request activation first.';
    root.querySelectorAll('[data-catalogue-approve],[data-catalogue-reject]').forEach(b=>{b.disabled=busy||!count||reasonLength<5;b.title=!count?'Select eligible requests below first.':reasonLength<5?'Enter a decision reason of at least 5 characters.':'';});
    root.querySelector('[data-catalogue-select-approvals]').disabled=busy||!eligible;
  };
  const history=async()=>{
    const data=await api('catalogue-setup/history/');if(!root.isConnected)return;
    approvalRows=data.approvals;
    const targetName=value=>{const id=value.slice(value.indexOf(':')+1);return report?.rows.find(r=>r.id===id)?.name||value;};
    root.querySelector('[data-catalogue-approvals]').innerHTML=`<div class="table-wrap"><table class="data-table finance-data-table"><thead><tr><th>Select</th><th>Catalogue entry</th><th>Requested by</th><th>Reason</th><th>Status</th></tr></thead><tbody>${data.approvals.map(a=>`<tr><td><input type="checkbox" data-catalogue-approval="${esc(a.id)}" aria-label="Select approval for ${esc(targetName(a.target))}" ${a.can_decide?'':'disabled'}></td><td>${esc(targetName(a.target))}</td><td>${esc(a.requester)}${String(a.requested_by)===String(user.id)?' (you; another administrator must review)':''}</td><td>${esc(a.reason)}</td><td>${esc(a.status)}</td></tr>`).join('')||'<tr><td colspan="5">No activation requests.</td></tr>'}</tbody></table></div>`;
    root.querySelector('[data-catalogue-history]').innerHTML=`<div class="table-wrap"><table class="data-table finance-data-table"><thead><tr><th>When</th><th>Actor ID</th><th>Action</th><th>Reason</th><th>Result</th></tr></thead><tbody>${data.events.map(e=>`<tr><td>${esc(new Date(e.occurred_at).toLocaleString('en-GB'))}</td><td>${esc(e.actor_id??'System')}</td><td>${esc(e.action)}</td><td>${esc(e.reason)}</td><td>${esc(e.metadata.created_count!==undefined?e.metadata.created_count+' created inactive':e.metadata.proposal_key||e.object_id)}</td></tr>`).join('')||'<tr><td colspan="5">No catalogue imports or activation events.</td></tr>'}</tbody></table></div>`;
    reviewState();
  };
  const safely=async action=>{if(busy)return;busy=true;root.setAttribute('aria-busy','true');root.querySelectorAll('button').forEach(b=>b.disabled=true);try{await action();}catch(error){if(root.isConnected)message(error.message);}finally{busy=false;root.removeAttribute('aria-busy');root.querySelectorAll('button').forEach(b=>b.disabled=false);reviewState();}};
  root.addEventListener('input',event=>{if(event.target.matches('[data-catalogue-decision-reason]'))reviewState();});
  root.addEventListener('change',event=>{
    if(event.target.matches('[data-catalogue-approval]'))reviewState();
    const box=event.target.closest('[data-catalogue-key]');if(box){box.checked?selected.add(box.dataset.catalogueKey):selected.delete(box.dataset.catalogueKey);root.querySelector('[data-catalogue-confirm]').checked=false;render();}
    if(event.target.matches('[data-catalogue-file]'))safely(async()=>{const file=event.target.files[0];if(!file)return;if(file.size>512*1024)throw Error('CSV exceeds 512KB.');csv=await file.text();await preview(true);await history();});
  });
  root.addEventListener('click',event=>{
    if(event.target.closest('[data-catalogue-select-approvals]')){root.querySelectorAll('[data-catalogue-approval]:not(:disabled)').forEach(b=>b.checked=true);reviewState();}
    if(report&&event.target.closest('[data-catalogue-inactive]')){selected=new Set(report.rows.filter(r=>r.id&&!r.is_active&&r.comparison_status!=='conflict').map(r=>r.key));root.querySelector('[data-catalogue-confirm]').checked=false;render();}

    if(report&&event.target.closest('[data-catalogue-select]')){selected=new Set(report.rows.filter(r=>r.comparison_status==='new').map(r=>r.key));root.querySelector('[data-catalogue-confirm]').checked=false;render();}
    if(event.target.closest('[data-catalogue-clear]')){selected.clear();root.querySelector('[data-catalogue-confirm]').checked=false;render();}
    if(event.target.closest('[data-catalogue-preview]'))safely(async()=>{await preview();await history();});
    if(event.target.closest('[data-catalogue-master]'))safely(async()=>{csv=null;root.querySelector('[data-catalogue-file]').value='';await preview(true);await history();});
    if(event.target.closest('[data-catalogue-export]'))safely(()=>download('catalogue-setup/csv/','hospital-catalogue-template.csv'));
    if(event.target.closest('[data-catalogue-import]'))safely(async()=>{
      if(!report||!selected.size||!root.querySelector('[data-catalogue-confirm]').checked)throw Error('Select entries and confirm the inactive-placeholder import first.');
      const result=await send('import',{...(csv===null?{}:{csv}),selected:[...selected],plan_token:report.plan_token,reason:reason(),confirmation:'IMPORT INACTIVE CATALOGUE'});
      await preview();await history();message(`${result.created_count} placeholders created inactive; ${result.existing_count} existing entries preserved. No services or prices were created.`);
    });
    if(event.target.closest('[data-catalogue-request]'))safely(async()=>{
      if(!report)throw Error('Load a catalogue preview first.');
      const targets=report.rows.filter(r=>selected.has(r.key)&&r.id&&!r.is_active).map(r=>r.kind+':'+r.id);
      if(!targets.length)throw Error('Select imported or existing inactive entries before requesting activation.');
      const result=await send('request-activation',{targets,reason:reason()});await history();message(`${result.approvals.length} activation requests await review by a different Super Administrator.`);
    });
    if(event.target.closest('[data-catalogue-approve],[data-catalogue-reject]'))safely(async()=>{
      const approvals=[...root.querySelectorAll('[data-catalogue-approval]:checked')].map(b=>b.dataset.catalogueApproval);
      if(!approvals.length)throw Error('Select requests that you are authorized to review.');
      const approved=!!event.target.closest('[data-catalogue-approve]');
      const result=await send('decide',{approvals,approved,reason:root.querySelector('[data-catalogue-decision-reason]').value.trim()});await preview();await history();message(`${result.decisions.length} review decisions recorded.`);
    });
  });
  await safely(async()=>{await preview(true);await history();});
}
