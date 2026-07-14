from __future__ import annotations
import hashlib,hmac,json,os,sqlite3,struct,subprocess,tempfile
from pathlib import Path
from .security import OpsError
MAGIC=b'RFXB1'
def _keys(passphrase:str,salt:bytes):return hashlib.scrypt(passphrase.encode(),salt=salt,n=2**14,r=8,p=1,dklen=64)
def create_backup(db:Path,out:Path,passphrase:str,schema_label:str)->dict:
 if len(passphrase)<16:raise OpsError('backup passphrase too short')
 salt=os.urandom(16);iv=os.urandom(16);keys=_keys(passphrase,salt);enc,mac=keys[:32],keys[32:]
 with tempfile.TemporaryDirectory() as directory:
  plain=Path(directory)/'db.sqlite';cipher=Path(directory)/'cipher.bin';source=sqlite3.connect(db);target=sqlite3.connect(plain);source.backup(target);target.close();source.close()
  subprocess.run(['openssl','enc','-aes-256-ctr','-K',enc.hex(),'-iv',iv.hex(),'-in',str(plain),'-out',str(cipher)],check=True,capture_output=True)
  payload=cipher.read_bytes();header={'schema':schema_label,'salt':salt.hex(),'iv':iv.hex(),'sha256':hashlib.sha256(plain.read_bytes()).hexdigest()};encoded=json.dumps(header,sort_keys=True,separators=(',',':')).encode();tag=hmac.new(mac,encoded+payload,hashlib.sha256).digest();out.write_bytes(MAGIC+struct.pack('>I',len(encoded))+encoded+payload+tag)
 return {'path':str(out),'schema':schema_label,'size':out.stat().st_size}
def restore_backup(src:Path,out_db:Path,passphrase:str,expected_schema:str)->None:
 data=src.read_bytes()
 if data[:5]!=MAGIC:raise OpsError('invalid backup format')
 length=struct.unpack('>I',data[5:9])[0];encoded=data[9:9+length];payload=data[9+length:-32];tag=data[-32:];header=json.loads(encoded);keys=_keys(passphrase,bytes.fromhex(header['salt']));enc,mac=keys[:32],keys[32:]
 if not hmac.compare_digest(tag,hmac.new(mac,encoded+payload,hashlib.sha256).digest()):raise OpsError('backup authentication failed')
 if header['schema']!=expected_schema:raise OpsError('backup schema mismatch')
 with tempfile.TemporaryDirectory() as directory:
  cipher=Path(directory)/'cipher';plain=Path(directory)/'plain.sqlite';cipher.write_bytes(payload);subprocess.run(['openssl','enc','-d','-aes-256-ctr','-K',enc.hex(),'-iv',header['iv'],'-in',str(cipher),'-out',str(plain)],check=True,capture_output=True)
  if hashlib.sha256(plain.read_bytes()).hexdigest()!=header['sha256']:raise OpsError('backup digest mismatch')
  connection=sqlite3.connect(plain);check=connection.execute('PRAGMA integrity_check').fetchone()[0];connection.close()
  if check!='ok':raise OpsError('restored sqlite integrity failed')
  out_db.parent.mkdir(parents=True,exist_ok=True);os.replace(plain,out_db)
