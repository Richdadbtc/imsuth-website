import {calculateOverhead} from './overhead.js';
export function calculateManualDrugs(rows,patientType='regular'){
 const names=new Set(),items=[];
 for(let i=0;i<rows.length;i++){
  const name=rows[i].name.trim(),key=name.toLowerCase();
  if(!name||name.length>200||/[\x00-\x1f\x7f]/.test(name))return {valid:false,error:'Enter a drug name for every item.'};
  if(names.has(key))return {valid:false,error:'Enter each drug once; use quantity for repeats.'};
  names.add(key);items.push({code:String(i),name,kind:'editable',unit:'unit'});
 }
 return calculateOverhead({label:'DRF drug',items},rows.map((row,i)=>({...row,code:String(i)})),patientType);
}
