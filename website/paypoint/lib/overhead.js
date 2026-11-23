const cents=value=>{const text=String(value??'');if(!/^\d+(\.\d{1,2})?$/.test(text))return null;const [whole,fraction='']=text.split('.');const result=Number(whole)*100+Number(fraction.padEnd(2,'0'));return Number.isSafeInteger(result)?result:null;};
export function calculateOverhead(catalogue,selections,patientType='regular'){
  const known=new Map((catalogue?.items||[]).map(row=>[row.code,row])),seen=new Set(),rows=[];
  let subtotalCents=0,surcharge=false;
  const fail=error=>({valid:false,error,rows,subtotalCents:0,surchargeCents:0,baseCents:0,discountCents:0,netCents:0});
  for(const selected of selections){
    const item=known.get(selected.code),quantity=Number(selected.quantity);
    if(!item||seen.has(selected.code))return fail('Select each service once and use quantity for repeats.');
    seen.add(selected.code);
    if(!Number.isInteger(quantity)||quantity<1||quantity>3650)return fail('Enter a quantity or number of days between 1 and 3650.');
    if(item.kind==='percentage'){surcharge=true;continue;}
    const price=cents(item.kind==='editable'?selected.unit_amount:item.amount);
    if(price===null||(item.kind==='editable'&&(price<=0||price>100000000000)))return fail('Enter a positive price with at most two decimal places for '+item.name+'.');
    const amount=item.kind==='tiered'?price+cents(item.subsequent_amount)*(quantity-1):price*quantity;
    if(!Number.isSafeInteger(amount)||!Number.isSafeInteger(subtotalCents+amount))return fail('The selected total is too large.');
    subtotalCents+=amount;rows.push({code:item.code,amountCents:amount});
  }
  if(!rows.length)return fail('Add at least one '+(catalogue?.label||'Over-head')+' item.');
  const surchargeCents=surcharge?Math.floor((subtotalCents+5)/10):0,baseCents=subtotalCents+surchargeCents;
  if(!Number.isSafeInteger(baseCents))return fail('The selected total is too large.');
  const discountCents=patientType==='regular'?0:Math.floor((baseCents+5)/10);
  return {valid:true,error:'',rows,subtotalCents,surchargeCents,baseCents,discountCents,netCents:baseCents-discountCents};
}
