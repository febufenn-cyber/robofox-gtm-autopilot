from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .security import authorize,redact,verify_session
class Handler(BaseHTTPRequestHandler):
 secret=b'';provider=lambda:{'status':'ok'}
 def do_GET(self):
  if self.path not in {'/health','/status'}:self.send_error(404);return
  if self.path=='/health':payload={'ok':True}
  else:
   try:s=verify_session(self.headers.get('Authorization','').removeprefix('Bearer '),self.secret,int(__import__('time').time()));authorize(s,'view');payload=redact(self.provider())
   except Exception:self.send_error(403);return
  data=json.dumps(payload).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def log_message(self,*args):pass
def serve(secret:bytes,provider,host='127.0.0.1',port=8765):
 if host not in {'127.0.0.1','localhost'}:raise ValueError('operator console must bind localhost')
 Handler.secret=secret;Handler.provider=provider;return ThreadingHTTPServer((host,port),Handler)
