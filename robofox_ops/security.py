from __future__ import annotations
import base64,hashlib,hmac,json
from typing import Any
class OpsError(ValueError):pass
PERMISSIONS={'founder':{'view','review','approve_internal','operate_simulator','admin'},'reviewer':{'view','review'},'operator':{'view','operate_simulator'},'read_only':{'view'}}
SENSITIVE={'secret','token','password','api_key','authorization','cookie','email','phone','address','name'}
def _b64(b:bytes)->str:return base64.urlsafe_b64encode(b).decode().rstrip('=')
def _unb64(s:str)->bytes:return base64.urlsafe_b64decode(s+'='*(-len(s)%4))
def issue_session(subject:str,role:str,secret:bytes,now:int,ttl_seconds:int=900)->str:
 if role not in PERMISSIONS or not 60<=ttl_seconds<=3600:raise OpsError('invalid session parameters')
 payload={'sub':subject,'role':role,'iat':now,'exp':now+ttl_seconds,'nonce':_b64(hashlib.sha256(f'{subject}:{now}'.encode()).digest()[:12])};body=_b64(json.dumps(payload,sort_keys=True,separators=(',',':')).encode());sig=_b64(hmac.new(secret,body.encode(),hashlib.sha256).digest());return body+'.'+sig
def verify_session(token:str,secret:bytes,now:int)->dict:
 try:body,sig=token.split('.',1);expected=_b64(hmac.new(secret,body.encode(),hashlib.sha256).digest())
 except Exception as exc:raise OpsError('invalid session') from exc
 if not hmac.compare_digest(sig,expected):raise OpsError('invalid session signature')
 payload=json.loads(_unb64(body))
 if payload.get('role') not in PERMISSIONS or now>=payload.get('exp',0) or now<payload.get('iat',0)-60:raise OpsError('expired or invalid session')
 return payload
def authorize(session:dict,permission:str)->None:
 if permission not in PERMISSIONS.get(session.get('role'),set()):raise OpsError('permission denied')
def redact(value:Any)->Any:
 if isinstance(value,dict):return {k:('[REDACTED]' if k.lower() in SENSITIVE else redact(v)) for k,v in value.items()}
 if isinstance(value,list):return [redact(v) for v in value]
 return value
