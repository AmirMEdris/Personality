"""Loopback-only application. Questionnaire answers stay in browser memory."""
import argparse,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .core import infer
ROOT=Path(__file__).resolve().parents[1]
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,code,body,mime='application/json'):
        raw=body if isinstance(body,bytes) else json.dumps(body,allow_nan=False).encode()
        self.send_response(code); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers(); self.wfile.write(raw)
    def safe_host(self):
        port=self.server.server_port
        return self.headers.get('Host') in [f'127.0.0.1:{port}',f'localhost:{port}']
    def do_GET(self):
        if not self.safe_host(): return self.send(403,{'error':'Local access only.'})
        routes={'/workbench':('web/workbench.html','text/html; charset=utf-8'),'/workbench.js':('web/workbench.js','text/javascript'),'/workbench.css':('web/workbench.css','text/css'),'/api/workbench':('artifacts/workbench/report.json','application/json'),'/':('web/index.html','text/html; charset=utf-8'),'/app.js':('web/app.js','text/javascript'),'/style.css':('web/style.css','text/css'),'/survey.json':('web/survey.json','application/json'),'/api/report':('artifacts/report.json','application/json'),'/api/examples':('artifacts/examples.json','application/json')}
        if self.path not in routes:return self.send(404,{'error':'Not found.'})
        path,mime=routes[self.path];self.send(200,(ROOT/path).read_bytes(),mime)
    def do_POST(self):
        origin=self.headers.get('Origin'); host=self.headers.get('Host')
        if not self.safe_host() or (origin and origin!='http://'+host):return self.send(403,{'error':'Local origin required.'})
        if self.path!='/api/predict':return self.send(404,{'error':'Not found.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=8192:raise ValueError('Request size invalid.')
            payload=json.loads(self.rfile.read(size));model=json.loads((ROOT/'artifacts/model.json').read_text())
            result=infer(model,payload['features'],payload['measurement']);self.send(200,result)
        except (ValueError,KeyError,TypeError,AttributeError) as e:self.send(400,{'error':str(e)})
def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);a=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    print(f'Personality Studio: http://127.0.0.1:{server.server_port} (Ctrl+C to stop)',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
