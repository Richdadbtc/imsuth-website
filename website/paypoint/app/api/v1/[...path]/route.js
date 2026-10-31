import {backendOrigin,proxyApi} from '../../../../lib/proxy.js';
export const runtime='nodejs';
export const dynamic='force-dynamic';
async function handler(request,{params}) {
  let origin;
  try{origin=backendOrigin(process.env.DJANGO_API_ORIGIN,process.env.NODE_ENV==='production');}
  catch{return Response.json({detail:'The application API has not been configured.'},{status:503});}
  return proxyApi(request,(await params).path,{origin});
}
export {handler as GET,handler as HEAD,handler as POST,handler as PUT,handler as PATCH,handler as DELETE,handler as OPTIONS};
