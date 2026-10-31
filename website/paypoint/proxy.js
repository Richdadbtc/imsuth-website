import {NextResponse} from 'next/server';

export function proxy(request) {
  const nonce=Buffer.from(crypto.randomUUID()).toString('base64');
  const development=process.env.NODE_ENV==='development';
  const policy=[
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${development?" 'unsafe-eval'":''}`,
    development?"style-src 'self' 'unsafe-inline'":`style-src 'self' 'nonce-${nonce}'`,
    "img-src 'self' data: blob:","font-src 'self'",`connect-src 'self'${development?' ws:':''}`,
    "object-src 'none'","base-uri 'self'","form-action 'self'","frame-ancestors 'none'",
  ].join('; ');
  const headers=new Headers(request.headers);headers.set('x-nonce',nonce);headers.set('Content-Security-Policy',policy);
  const response=NextResponse.next({request:{headers}});
  response.headers.set('Content-Security-Policy',policy);
  response.headers.set('Cache-Control','private, no-store');
  return response;
}
export const config={matcher:['/((?!api|_next/static|_next/image|images|favicon.ico).*)']};
