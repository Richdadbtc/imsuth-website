"""Local-only public-site server with same-origin PayPoint API forwarding.

Run from the project root: backend/.venv/bin/python backend/dev_proxy.py
Start Django separately on 127.0.0.1:8012. No credentials or records are created.
"""
import argparse
from functools import partial
from http.client import HTTPConnection
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOP_HEADERS={'connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','upgrade'}
class LocalHandler(SimpleHTTPRequestHandler):
    backend_port=8012
    def proxy(self):
        if not (self.path.startswith('/paypoint/api/') or self.path.startswith('/api/')):
            return False
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<0 or length>6*1024*1024:
                self.send_error(413,'Request is too large');return True
            if self.headers.get('Transfer-Encoding'):
                self.send_error(400,'Use a content length');return True
            body=self.rfile.read(length) if length else None
            headers={k:v for k,v in self.headers.items() if k.lower() not in HOP_HEADERS}
            headers['Host']=self.headers.get('Host','127.0.0.1:5500')
            connection=HTTPConnection('127.0.0.1',self.backend_port,timeout=30)
            try:
                connection.request(self.command,self.path,body,headers)
                response=connection.getresponse();payload=response.read()
                self.send_response(response.status,response.reason)
                for k,v in response.getheaders():
                    if k.lower() not in HOP_HEADERS|{'content-length','server','date'}:self.send_header(k,v)
                self.send_header('Content-Length',str(len(payload)))
                self.end_headers()
                if self.command!='HEAD':self.wfile.write(payload)
            finally:connection.close()
        except (OSError,ValueError):self.send_error(502,'PayPoint backend is unavailable')
        return True
    def do_GET(self):
        if not self.proxy():super().do_GET()
    def do_HEAD(self):
        if not self.proxy():super().do_HEAD()
    def mutation(self):
        if not self.proxy():self.send_error(405,'Only PayPoint API writes are supported')
    do_POST=do_PUT=do_PATCH=do_DELETE=do_OPTIONS=mutation
    def log_message(self,format,*args):
        # Avoid storing patient searches, recovery tokens or reference query strings.
        if '/api/' not in self.path:super().log_message(format,*args)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=5500)
    parser.add_argument('--backend-port',type=int,default=8012)
    args=parser.parse_args()
    LocalHandler.backend_port=args.backend_port
    root=Path(__file__).resolve().parent.parent
    print(f'Local website: http://127.0.0.1:{args.port}/website/paypoint/index.html',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),partial(LocalHandler,directory=str(root))).serve_forever()
