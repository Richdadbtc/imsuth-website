import {calculateOverhead} from '../lib/overhead.js';
export function mountOverheadPicker(root,{catalogue,escapeHtml,money,onChange,getPatientType=()=> 'regular'}){
  const label=catalogue?.label||'Over-head';
  const selected=[],items=catalogue?.items||[],byCode=new Map(items.map(item=>[item.code,item]));
  root.innerHTML=`<p data-catalogue-source></p><label>Find an item<input type="search" data-catalogue-search placeholder="Type a name or item number"></label><div class="overhead-add"><label>${escapeHtml(label)} items<select data-overhead-choice><option value="">Select a service to add</option></select></label><button type="button" class="pending-outline" data-overhead-add>Add service</button></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Selected service</th><th>${items.some(item=>item.unit==='day'||item.unit==='week')?'Quantity / days / weeks':'Quantity'}</th><th>Unit price (₦)</th><th>Total (₦)</th><th></th></tr></thead><tbody data-overhead-rows></tbody></table></div><p data-overhead-status role="status"></p><p data-overhead-totals></p>`;
  const choice=root.querySelector('[data-overhead-choice]'),body=root.querySelector('[data-overhead-rows]');
  root.querySelector('[data-catalogue-source]').textContent=catalogue?.source_note||'';
  root.querySelector('[data-catalogue-source]').hidden=!catalogue?.source_note;
  const read=()=>calculateOverhead(catalogue,selected,getPatientType());
  const update=()=>{
    const state=read();
    root.querySelector('[data-overhead-status]').textContent=items.length?(state.valid?(state.baseCents===0?'No payment is due. A paid receipt requires a positive total.':''):state.error):label+' items are unavailable. Refresh or contact your administrator.';
    root.querySelector('[data-overhead-totals]').textContent=state.valid?`Subtotal: ${money(state.subtotalCents/100)}${items.some(item=>item.kind==='percentage')?' · Surcharge: '+money(state.surchargeCents/100):''} · Full total: ${money(state.baseCents/100)}`:'';
    for(const row of body.querySelectorAll('[data-overhead-row]')){
      const item=byCode.get(row.dataset.overheadRow),amount=state.rows.find(value=>value.code===item.code)?.amountCents;
      row.querySelector('[data-line-total]').textContent=item.kind==='percentage'?(state.valid?money(state.surchargeCents/100):'—'):amount===undefined?'—':money(amount/100);
    }
    onChange(state);
  };
  const draw=()=>{
    const groups=[...new Set(items.map(item=>item.group))];
    choice.innerHTML='<option value="">Select a service to add</option>'+groups.map(group=>`<optgroup label="${escapeHtml(group)}">${items.filter(item=>item.group===group&&(!root.querySelector('[data-catalogue-search]').value||`${item.source_number||''} ${item.name}`.toLowerCase().includes(root.querySelector('[data-catalogue-search]').value.toLowerCase()))).map(item=>`<option value="${escapeHtml(item.code)}" ${selected.some(row=>row.code===item.code)?'disabled':''}>${item.source_number?item.source_number+'. ':''}${escapeHtml(item.name)}${item.kind==='editable'?' — Enter price':item.kind==='percentage'?'':item.kind==='tiered'?` — first day ${money(item.amount)}, then ${money(item.subsequent_amount)} / day`:` — ${money(item.amount)}${item.unit==='unit'?'':' / '+item.unit}`}</option>`).join('')}</optgroup>`).join('');
    body.innerHTML=selected.map(row=>{const item=byCode.get(row.code);return `<tr data-overhead-row="${escapeHtml(row.code)}"><td>${escapeHtml(item.name)}${item.kind==='tiered'?`<small>First day ${money(item.amount)}; each subsequent day ${money(item.subsequent_amount)}</small>`:''}</td><td>${item.kind==='percentage'?'10% of all selected items':`<label>${item.unit==='day'?'Total days':item.unit==='week'?'Weeks':'Quantity'}<input data-item-quantity type="number" min="1" max="3650" step="1" required value="${escapeHtml(row.quantity)}" aria-label="${escapeHtml(item.name)} ${item.unit==='day'?'days':item.unit==='week'?'weeks':'quantity'}"></label>`}</td><td>${item.kind==='editable'?`<input data-item-price type="number" min="0.01" max="1000000000" step="0.01" required value="${escapeHtml(row.unit_amount??'')}" aria-label="${escapeHtml(item.name)} price" placeholder="Enter price">`:item.kind==='percentage'?'10%':money(item.amount)}</td><td data-line-total>—</td><td><button type="button" class="pending-outline" data-overhead-remove="${escapeHtml(row.code)}" aria-label="Remove ${escapeHtml(item.name)}">Remove</button></td></tr>`;}).join('')||`<tr><td colspan="5">No ${escapeHtml(label)} items selected.</td></tr>`;
    update();
  };
  root.querySelector('[data-catalogue-search]').addEventListener('input',draw);
  root.querySelector('[data-overhead-add]').addEventListener('click',()=>{if(!byCode.has(choice.value)||selected.some(row=>row.code===choice.value))return;selected.push({code:choice.value,quantity:1});draw();});
  root.addEventListener('click',event=>{const button=event.target.closest('[data-overhead-remove]');if(!button)return;const index=selected.findIndex(row=>row.code===button.dataset.overheadRemove);if(index>=0){selected.splice(index,1);draw();}});
  root.addEventListener('input',event=>{const tr=event.target.closest('[data-overhead-row]');if(!tr)return;const row=selected.find(item=>item.code===tr.dataset.overheadRow);if(event.target.matches('[data-item-quantity]'))row.quantity=event.target.value;if(event.target.matches('[data-item-price]'))row.unit_amount=event.target.value;update();});
  draw();return {read,selections:()=>selected.map(row=>({...row,quantity:Number(row.quantity)}))};
}
