import {calculateManualDrugs} from '../lib/manual-drugs.js';
export function mountManualDrugPicker(root,{escapeHtml,money,onChange,getPatientType}){
 const rows=[{name:'',quantity:1,unit_amount:''}];
 root.innerHTML='<p>Enter each drug name and its unit price. Add more drugs when needed.</p><div data-drug-rows></div><button type="button" class="pending-outline" data-drug-add>Add another drug</button><p data-drug-status role="status"></p>';
 const read=()=>calculateManualDrugs(rows,getPatientType());
 const update=()=>{
  const state=read();root.querySelector('[data-drug-status]').textContent=state.valid?`Full total: ${money(state.baseCents/100)} · Amount to pay: ${money(state.netCents/100)}`:state.error;
  onChange(state);
 };
 const draw=()=>{
  root.querySelector('[data-drug-rows]').innerHTML=rows.map((row,i)=>`<div class="manual-drug-row" data-drug-row="${i}"><label>Drug name<input data-drug-name required maxlength="200" value="${escapeHtml(row.name)}" placeholder="Enter drug name"></label><label>Unit price (₦)<input data-drug-price type="number" min="0.01" max="1000000000" step="0.01" required value="${escapeHtml(row.unit_amount)}" placeholder="Enter price"></label><label>Quantity<input data-drug-quantity type="number" min="1" max="3650" step="1" required value="${escapeHtml(row.quantity)}"></label><button type="button" class="pending-outline" data-drug-remove="${i}" ${rows.length===1?'disabled':''}>Remove</button></div>`).join('');
  root.querySelector('[data-drug-add]').disabled=rows.length>=322;update();
 };
 root.addEventListener('input',event=>{
  const container=event.target.closest('[data-drug-row]');if(!container)return;
  const row=rows[Number(container.dataset.drugRow)];
  if(event.target.matches('[data-drug-name]'))row.name=event.target.value;
  if(event.target.matches('[data-drug-price]'))row.unit_amount=event.target.value;
  if(event.target.matches('[data-drug-quantity]'))row.quantity=event.target.value;
  update();
 });
 root.querySelector('[data-drug-add]').addEventListener('click',()=>{if(rows.length>=322)return;rows.push({name:'',quantity:1,unit_amount:''});draw();root.querySelector('[data-drug-rows]').lastElementChild.querySelector('input').focus();});
 root.addEventListener('click',event=>{const button=event.target.closest('[data-drug-remove]');if(!button||rows.length===1)return;rows.splice(Number(button.dataset.drugRemove),1);draw();});
 draw();return {read,refresh:update,selections:()=>rows.map(row=>({name:row.name.trim(),quantity:Number(row.quantity),unit_amount:row.unit_amount}))};
}
