export function defaultOverviewDates(now=new Date()){
 const parts=new Intl.DateTimeFormat('en-CA',{timeZone:'Africa/Lagos',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
 const part=name=>parts.find(p=>p.type===name).value;
 const date_to=`${part('year')}-${part('month')}-${part('day')}`,start=new Date(date_to+'T00:00:00Z');start.setUTCDate(start.getUTCDate()-29);
 return {date_from:start.toISOString().slice(0,10),date_to};
}
export function overviewDateQuery({date_from,date_to}){
 const valid=value=>/^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value))&&new Date(value+'T00:00:00Z').toISOString().slice(0,10)===value;
 if(!valid(date_from)||!valid(date_to))throw new Error('Select valid From and To dates.');
 if(date_from>date_to)throw new Error('From date must not be later than To date.');
 return new URLSearchParams({period:'custom',date_from,date_to});
}
