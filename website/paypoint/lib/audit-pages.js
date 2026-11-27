// Fetch exactly one audit page; never walk the entire history on screen load.
export async function loadAuditPage(api,{period='30',page=1,pageSize=10}={}){
 const query=new URLSearchParams({period:period==='1'?'today':period,page:String(page),page_size:String(pageSize)});
 const data=await api('audit-logs/?'+query);
 return {rows:Array.isArray(data.results)?data.results:[],count:data.count??0,next:Boolean(data.next),previous:Boolean(data.previous)};
}
