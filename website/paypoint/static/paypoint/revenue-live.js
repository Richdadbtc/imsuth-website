/* Same-origin vanilla ES6 helpers. Financial totals come from the server. */
import {api} from './api.js?v=20261024-live1';
export const requestKey = () => crypto.randomUUID();
export async function submitJSON(path, body, method='POST') {
  return api(path,{method,body:JSON.stringify(body)});
}
export async function refreshOverview(root, escapeHtml, moneyWhole) {
  const select=root.querySelector('[data-overview-period]');let sequence=0;
  const refresh=async()=>{const current=++sequence,period=select.value==='1'?'today':select.value,query='?period='+encodeURIComponent(period);
    try {
      const [summary,channels,departments,statuses,alerts]=await Promise.all(['summary','collections-by-channel','collections-by-department','payment-status','alerts-summary'].map(p=>api('dashboard/'+p+'/'+query)));
      if(current!==sequence||!root.isConnected)return;
      root.querySelector('[data-overview-kpis]').innerHTML=[['Verified Collection',moneyWhole(summary.verified_collections),'Confirmation date · NGN'],['Total Attempts',summary.transactions,'Creation date'],['Verified Transactions',summary.verified_transactions,'Confirmation date'],['Pending / Unverified',moneyWhole(summary.pending_amount),'Not collected revenue'],['Departments',summary.active_departments,'Active, permitted departments']].map(([name,value,note])=>`<article><div><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></div></article>`).join('');
      const colours=['#1687ff','#00a995','#ff922c','#f53883','#a55bff'];
      const donut=(rows,total,key,valueKey,center)=>{let angle=0;const stops=rows.map((r,i)=>{const start=angle;angle+=total?Number(r[valueKey])/total*100:0;return `${colours[i%colours.length]} ${start}% ${angle}%`;});return `<div class="finance-donut" data-chart-background="${total?`conic-gradient(${stops.join(',')})`:'#e8eef5'}"><div><strong>${escapeHtml(center)}</strong><span>Selected period</span></div></div><div class="finance-department-legend">${rows.map((r,i)=>`<div><span data-chart-colour="${colours[i%colours.length]}">${escapeHtml(r[key])}</span><b>${valueKey==='amount'?moneyWhole(r[valueKey]):r[valueKey]}</b></div>`).join('')||'<p>No activity in this period.</p>'}</div>`;};
      root.querySelector('[data-overview-channels]').innerHTML=donut(channels,Number(summary.verified_collections),'channel','amount',moneyWhole(summary.verified_collections));
      const max=Math.max(1,...departments.map(r=>Number(r.amount)));
      root.querySelector('[data-overview-departments]').innerHTML=departments.slice(0,7).map((r,i)=>`<div class="overview-department-row"><span>${escapeHtml(r.invoice__department__name)}</span><div><i data-chart-width="${Number(r.amount)/max*100}%" data-chart-background="${colours[i%colours.length]}"></i></div><b>${moneyWhole(r.amount)}</b></div>`).join('')||'<p>No departmental collections.</p>';
      root.querySelector('[data-overview-status]').innerHTML=donut(statuses,summary.transactions,'status','count',String(summary.transactions));
      root.querySelector('[data-overview-alert-count]').textContent=String(alerts.open+alerts.in_review);
      root.querySelector('[data-overview-alerts]').innerHTML=Object.entries(alerts).map(([k,n])=>`<a class="overview-alert-row" href="#alerts"><span>${escapeHtml(k.replaceAll('_',' '))}</span><b>${n}</b></a>`).join('');
    }catch(error){const note=root.querySelector('.overview-preview-note');note.textContent=error.message;root.querySelector('[data-overview-kpis]').textContent='Authoritative totals could not be loaded.';}
  };select.addEventListener('change',refresh);await refresh();
}

export function watchPaymentStatus(id, isActive, onChange, holder) {
  let attempts=0,timer,busy=false;
  const button=document.createElement('button');button.type='button';button.className='pending-outline';button.textContent='Check verification status';
  if(holder)holder.replaceChildren(button);
  const poll=async()=>{
    if(!isActive()||busy)return;busy=true;button.disabled=true;clearTimeout(timer);
    try {
      const result=await api(`payments/${encodeURIComponent(id)}/verification-status/`);
      if(!isActive())return;
      await onChange(result);
      if(['pending','awaiting_offline_verification','review_required'].includes(result.status)&&++attempts<20)timer=setTimeout(poll,3000);
      else if(result.status==='confirmed')button.hidden=true;
    }catch(error){if(isActive())onChange({error:error.message});}
    finally{busy=false;button.disabled=false;}
  };
  button.addEventListener('click',()=>{attempts=0;poll();});timer=setTimeout(poll,3000);
}

export async function mountTariffProposals(root, user, reload, escapeHtml, moneyWhole) {
  const panel=document.createElement('section');panel.className='finance-card';root.querySelector('.sp-aside, aside').append(panel);
  let page=1,selection=null;
  const render=async()=>{const data=await api(`tariff-proposals/?page=${page}`);
    panel.innerHTML=`<h2>Tariff Proposals</h2><p>Independent approval is required. Existing invoice prices remain unchanged.</p><div class="table-wrap"><table class="data-table finance-data-table"><thead><tr><th>Service</th><th>Amount</th><th>Effective from</th><th>Status</th><th>Decision</th></tr></thead><tbody>${data.results.map(p=>{const allowed=['finance','management','super_admin'].includes(user.role)&&String(p.requested_by)!==String(user.id)&&p.status==='pending';return `<tr><td>${escapeHtml(p.service_name||p.service)}</td><td>${moneyWhole(p.amount)}</td><td>${escapeHtml(p.effective_from)}</td><td>${escapeHtml(p.status)}</td><td>${['approve','reject'].map(action=>`<button type="button" class="pending-outline" data-tp-id="${p.id}" data-tp-decision="${action}" ${allowed?'':'disabled title="Requires a pending proposal and an independent authorized approver."'}>${action}</button>`).join('')}</td></tr>`;}).join('')||'<tr><td colspan="5">No proposals.</td></tr>'}</tbody></table></div><div class="pending-pagination"><button data-tp-page="${page-1}" ${data.previous?'':'disabled'}>Previous</button><span>${page} · ${data.count} proposals</span><button data-tp-page="${page+1}" ${data.next?'':'disabled'}>Next</button></div><div data-tp-form></div><p data-tp-message role="status"></p>`;};
  panel.addEventListener('click',async event=>{const button=event.target.closest('[data-tp-id]'),pager=event.target.closest('[data-tp-page]');try{if(pager&&!pager.disabled){page=Number(pager.dataset.tpPage);await render();}if(button&&!button.disabled){selection={id:button.dataset.tpId,action:button.dataset.tpDecision};panel.querySelector('[data-tp-form]').innerHTML=`<form><label>Decision notes<textarea name="notes" required minlength="5" maxlength="2000"></textarea></label><button class="pending-verify">Confirm ${escapeHtml(selection.action)}</button></form>`;}}catch(error){panel.querySelector('[data-tp-message]').textContent=error.message;}});
  panel.addEventListener('submit',async event=>{event.preventDefault();if(!selection)return;const button=event.target.querySelector('button');button.disabled=true;try{await submitJSON(`tariff-proposals/${selection.id}/${selection.action}/`,{notes:new FormData(event.target).get('notes')});await reload();}catch(error){panel.querySelector('[data-tp-message]').textContent=error.message;button.disabled=false;}});
  try{await render();}catch(error){panel.textContent=error.message;}
}

export function mountCashEvidence(root, reload, escapeHtml, moneyWhole) {
  let generation=0,dirty=false;
  root.querySelector('dialog').addEventListener('close',()=>{generation++;if(dirty&&root.isConnected){dirty=false;reload();}});
  root.addEventListener('click',async event=>{
    const button=event.target.closest('[data-cp-point]');if(!button)return;
    const point=button.dataset.cpPoint,version=++generation,holder=root.querySelector('[data-cp-dialog]');
    holder.innerHTML='<h2>Cash Collection Evidence</h2><p role="status">Loading verified payments and recorded evidence…</p>';
    try{
      const [rows,payments]=await Promise.all([api(`cash-points/${point}/collections/`),api('payments/?channel=cash&status=confirmed&page_size=100')]);
      if(version!==generation||!root.isConnected)return;
      holder.innerHTML=`<h2>Cash Collection Evidence</h2><p>Authorization, verified cash collection and bank deposit are separate. Bank deposit status: <strong>Not certified</strong>.</p><div class="table-wrap"><table class="data-table finance-data-table"><thead><tr><th>Evidence reference</th><th>Amount</th><th>Deposit status</th><th>Attachment</th></tr></thead><tbody>${rows.results.map(r=>`<tr><td>${escapeHtml(r.evidence_reference)}</td><td>${moneyWhole(r.amount)}</td><td>Not certified</td><td>${r.has_attachment?`<a href="${escapeHtml(window.PAYPOINT_CONFIG.apiBase)}cash-points/${point}/collections/${r.id}/attachment/">Download evidence</a>`:'None'}</td></tr>`).join('')||'<tr><td colspan="4">No evidence recorded.</td></tr>'}</tbody></table></div><form class="cp-order-form" data-cash-evidence="${point}"><label>Verified cash payment<select name="payment" required><option value="">Select a verified cash payment</option>${payments.results.map(p=>`<option value="${p.id}">${escapeHtml(p.reference)} · ${moneyWhole(p.amount)}</option>`).join('')}</select></label><label>Evidence reference<input name="evidence_reference" required minlength="5" maxlength="160"></label><label>Attachment (optional; PDF, PNG, JPG up to 2MB)<input name="file" type="file" accept=".pdf,.png,.jpg,.jpeg"></label><button class="pending-verify">Record Cash Evidence</button><p role="status"></p></form><p>Only a confirmed cash payment in this point’s department is eligible. A pending payment cannot be confirmed here.</p>`;
    }catch(error){holder.textContent=error.message;}
  });
  root.addEventListener('submit',async event=>{const form=event.target;if(!form.matches('[data-cash-evidence]'))return;event.preventDefault();const data=new FormData(form),button=form.querySelector('button'),message=form.querySelector('[role=status]');button.disabled=true;
    try{const point=form.dataset.cashEvidence,record=form.dataset.recordId?{id:form.dataset.recordId}:await submitJSON(`cash-points/${point}/collections/`,{payment:data.get('payment'),evidence_reference:data.get('evidence_reference')});form.dataset.recordId=record.id;dirty=true;const file=data.get('file');if(file?.size){const attachment=new FormData();attachment.append('file',file);await api(`cash-points/${point}/collections/${record.id}/attachment/`,{method:'POST',body:attachment});}message.textContent='Evidence recorded. Bank deposit remains unverified.';button.hidden=true;button.disabled=false;}
    catch(error){message.textContent=(dirty?'Evidence was recorded, but its attachment was not saved. Reopen the evidence record to check it. ':'')+error.message;button.disabled=false;}
  });
}

export async function mountOverviewTransactions(root, escapeHtml, moneyWhole) {
  let page=1,search='',sequence=0;
  const period=root.querySelector('[data-overview-period]');
  const render=async()=>{const version=++sequence,params=new URLSearchParams({period:period.value==='1'?'today':period.value,page:String(page),page_size:'10',search});
    root.querySelector('[data-overview-table]').innerHTML='<p role="status">Loading authorized transactions…</p>';
    try{const data=await api('dashboard/recent-transactions/?'+params);if(version!==sequence||!root.isConnected)return;
      root.querySelector('[data-overview-table]').innerHTML=`<div class="table-wrap"><table class="data-table finance-data-table"><thead><tr><th>#</th><th>Date & Time</th><th>Patient Name</th><th>Department</th><th>Service</th><th>Channel</th><th>Amount (₦)</th><th>Status</th><th>Receipt No.</th><th>Actions</th></tr></thead><tbody>${data.results.map((p,index)=>`<tr><td>${(page-1)*10+index+1}</td><td>${escapeHtml(new Date(p.created_at).toLocaleString("en-GB",{timeZone:"Africa/Lagos"}))}</td><td>${escapeHtml(p.patient_name)}</td><td>${escapeHtml(p.department)}</td><td>${escapeHtml(p.service_summary||"—")}</td><td>${escapeHtml(p.channel)}</td><td>${moneyWhole(p.amount)}</td><td>${escapeHtml(p.status)}</td><td>${escapeHtml(p.receipt_number||"Not issued")}</td><td><button class="pending-outline" data-live-transaction="${p.id}">View</button></td></tr>`).join('')||'<tr><td colspan="10">No transactions match these filters.</td></tr>'}</tbody></table></div>`;
      root.querySelector('[data-overview-count]').textContent=`Showing ${data.count?(page-1)*10+1:0} to ${Math.min(page*10,data.count)} of ${data.count} transactions`;
      root.querySelector('[data-overview-pages]').innerHTML=`<button data-live-transactions-page="${page-1}" ${data.previous?'':'disabled'} aria-label="Previous transaction page">Previous</button><span> ${page} </span><button data-live-transactions-page="${page+1}" ${data.next?'':'disabled'} aria-label="Next transaction page">Next</button>`;
    }catch(error){root.querySelector('[data-overview-table]').textContent=error.message;}};
  root.addEventListener('click',async event=>{const view=event.target.closest('[data-live-transaction]');if(view){try{const p=await api(`payments/${view.dataset.liveTransaction}/`);root.querySelector('[data-overview-detail]').innerHTML=`<h2>Transaction Details</h2><p>${escapeHtml(p.reference)}</p><p>${escapeHtml(p.patient_name)} · ${escapeHtml(p.department)}</p><p>${moneyWhole(p.amount)} · ${escapeHtml(p.status)}</p><p>${escapeHtml(p.service_summary)}</p>`;root.querySelector('dialog').showModal();}catch(error){root.querySelector('[data-overview-table]').textContent=error.message;}}const button=event.target.closest('[data-live-transactions-page]');if(button&&!button.disabled){page=Number(button.dataset.liveTransactionsPage);render();}});
  period.addEventListener('change',()=>{page=1;render();});let debounce;
  root.addEventListener('revenue-search',event=>{clearTimeout(debounce);debounce=setTimeout(()=>{search=event.detail;page=1;render();},250);});await render();
}

export async function mountDepartmentDirectory(root, escapeHtml, moneyWhole, user={}) {
  let page=1,sequence=0;const form=root.querySelector('[data-rd-filters]')||root.querySelector('form'),period=root.querySelector('[data-rd-period]');
  const render=async()=>{const version=++sequence,data=new FormData(form),status=data.get('status')||'',search=data.get('search')||'',sort=data.get('sort')||'amount',params=new URLSearchParams({page:String(page),page_size:'10',search,period:period.value==='1'?'today':period.value,ordering:({name:'name',amount:'-collection',transactions:'-transactions',pending:'-pending'})[sort]||'-collection'});if(status)params.set('is_active',status==='active'?'true':'false');
    root.querySelector('[data-rd-table]').innerHTML='<p role="status">Loading authorized departments…</p>';
    try{const [rows,summary]=await Promise.all([api('departments/?'+params),api('departments/analytics/?'+params)]);if(version!==sequence||!root.isConnected)return;
      const amounts=new Map(summary.results.map(r=>[String(r.invoice__department_id),r]));
      root.querySelector('[data-rd-table]').innerHTML=`<div class="table-wrap"><table class="data-table finance-data-table"><thead><tr><th>#</th><th>Department</th><th>Total Collection</th><th>Transactions</th><th>Average Amount</th><th>Pending</th><th>Last Transaction</th><th>Status</th><th>Actions</th></tr></thead><tbody>${rows.results.map((d,index)=>{const r=amounts.get(String(d.id))||{};return `<tr><td>${(page-1)*10+index+1}</td><td>${escapeHtml(d.name)}</td><td>${moneyWhole(r.collected||0)}</td><td>${r.count||0}</td><td>${moneyWhole(r.average||0)}</td><td>${moneyWhole(r.pending||0)}</td><td>${r.last?escapeHtml(new Date(r.last).toLocaleString('en-GB',{timeZone:'Africa/Lagos'})):'No transactions'}</td><td>${d.is_active?'Active':'Inactive'}</td><td><button class="pending-outline" data-live-department="${d.id}">View</button></td></tr>`;}).join('')||'<tr><td colspan="9">No departments match these filters.</td></tr>'}</tbody></table></div>`;
      root.querySelector('[data-rd-count]').textContent=`Showing ${rows.count?(page-1)*10+1:0} to ${Math.min(page*10,rows.count)} of ${rows.count} departments`;
      root.querySelector('[data-rd-pages]').innerHTML=`<button data-live-department-page="${page-1}" ${rows.previous?'':'disabled'} aria-label="Previous department page">Previous</button><span> ${page} </span><button data-live-department-page="${page+1}" ${rows.next?'':'disabled'} aria-label="Next department page">Next</button>`;
      root.querySelector('[data-rd-kpis]').innerHTML=[['Total Departments',summary.department_count],['Total Collections',moneyWhole(summary.collected)],['Total Transactions',summary.transactions],['Departments with Collections',summary.departments_with_collections]].map(([name,value])=>`<article><div><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong><small>Authorized server results</small></div></article>`).join('');
      const ranked=[...summary.results].sort((a,b)=>Number(b.collected||0)-Number(a.collected||0)),max=Math.max(1,...ranked.map(r=>Number(r.collected||0))),colours=['#1687ff','#00a995','#ff922c','#f53883','#a55bff'];
      root.querySelector('[data-rd-bars]').innerHTML=ranked.slice(0,7).map((r,i)=>`<div class="overview-department-row"><span>${escapeHtml(r.invoice__department__name)}</span><div><i data-chart-width="${Number(r.collected||0)/max*100}%" data-chart-background="${colours[i%colours.length]}"></i></div><b>${moneyWhole(r.collected||0)}</b></div>`).join('')||'<p>No collections in this period.</p>';
      const total=Number(summary.collected),groups=[['Top 3 Departments',ranked.slice(0,3)],['Next 5 Departments',ranked.slice(3,8)],['Others',ranked.slice(8)]].map(([name,rows])=>({name,amount:rows.reduce((n,r)=>n+Number(r.collected||0),0)}));let angle=0;const stops=groups.map((g,i)=>{const start=angle;angle+=total?g.amount/total*100:0;return `${colours[i]} ${start}% ${angle}%`;});root.querySelector('[data-rd-performance]').innerHTML=`<div class="finance-donut" data-chart-background="${total?`conic-gradient(${stops.join(',')})`:'#e8eef5'}"><div><strong>${moneyWhole(summary.collected)}</strong><span>Total Collection</span></div></div><div class="finance-department-legend">${groups.map((g,i)=>`<div><span data-chart-colour="${colours[i]}">${g.name}</span><b>${total?(g.amount/total*100).toFixed(1):'0.0'}%</b></div>`).join('')}</div>`;

    }catch(error){root.querySelector('[data-rd-table]').textContent=error.message;}};
  form.addEventListener('submit',event=>{event.preventDefault();page=1;render();});form.addEventListener('reset',()=>setTimeout(()=>{page=1;render();},0));period.addEventListener('change',()=>{page=1;render();});
  root.addEventListener('click',async event=>{const pager=event.target.closest('[data-live-department-page]'),view=event.target.closest('[data-live-department]');if(pager&&!pager.disabled){page=Number(pager.dataset.liveDepartmentPage);render();}if(view){try{const d=await api(`departments/${view.dataset.liveDepartment}/`),dialog=root.querySelector('dialog');root.querySelector('[data-rd-dialog]').innerHTML=`<h2>${escapeHtml(d.name)}</h2><p>${escapeHtml(d.code)}</p><p>${escapeHtml(d.description)}</p>${['finance','super_admin'].includes(user.role)?`<form class="live-form" data-department-edit><label>Department Name<input name="name" required maxlength="120" value="${escapeHtml(d.name)}"></label><label>Department Code<input name="code" required maxlength="24" value="${escapeHtml(d.code)}"></label><label>Description<textarea name="description">${escapeHtml(d.description)}</textarea></label><label>Active<input name="active" type="checkbox" ${d.is_active?'checked':''}></label><button class="pending-verify">Save Department</button><p role="status"></p></form>`:''}`;const edit=root.querySelector('[data-department-edit]');if(edit)edit.addEventListener('submit',async event=>{event.preventDefault();const button=edit.querySelector('button');button.disabled=true;try{const values=Object.fromEntries(new FormData(edit));await submitJSON(`departments/${d.id}/`,{name:values.name,code:values.code,description:values.description,is_active:edit.elements.active.checked},'PATCH');dialog.close();await render();}catch(error){edit.querySelector('[role=status]').textContent=error.message;}finally{button.disabled=false;}});dialog.showModal();}catch(error){root.querySelector('[data-rd-table]').textContent=error.message;}}});
  root.addEventListener('revenue-search',event=>{form.querySelector('[name=search]').value=event.detail;page=1;render();});await render();
}
