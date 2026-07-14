from __future__ import annotations
import json,sqlite3,uuid
from .security import OpsError
SCHEMA="""CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,idempotency_key TEXT UNIQUE NOT NULL,kind TEXT NOT NULL,payload_json TEXT NOT NULL,status TEXT NOT NULL,irreversible INTEGER NOT NULL,max_attempts INTEGER NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,lease_owner TEXT,lease_until INTEGER,last_error TEXT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL);"""
def install(c):c.executescript(SCHEMA);c.commit()
def enqueue(c,idempotency_key,kind,payload,now,irreversible=False,max_attempts=3):
 if irreversible:max_attempts=1
 ident='JOB-'+uuid.uuid4().hex[:16].upper()
 with c:c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(ident,idempotency_key,kind,json.dumps(payload,sort_keys=True),'QUEUED',int(irreversible),max_attempts,0,None,None,None,now,now))
 return ident
def claim(c,worker,now,lease_seconds=60):
 with c:
  row=c.execute("SELECT id FROM jobs WHERE status IN ('QUEUED','RETRY') AND (lease_until IS NULL OR lease_until<=?) AND attempts<max_attempts ORDER BY created_at,id LIMIT 1",(now,)).fetchone()
  if not row:return None
  changed=c.execute("UPDATE jobs SET status='LEASED',lease_owner=?,lease_until=?,attempts=attempts+1,updated_at=? WHERE id=? AND (lease_until IS NULL OR lease_until<=?)",(worker,now+lease_seconds,now,row[0],now))
  if changed.rowcount!=1:return None
 return row[0]
def heartbeat(c,job,worker,now,lease_seconds=60):
 with c:
  if c.execute("UPDATE jobs SET lease_until=?,updated_at=? WHERE id=? AND status='LEASED' AND lease_owner=? AND lease_until>?",(now+lease_seconds,now,job,worker,now)).rowcount!=1:raise OpsError('job lease lost')
def complete(c,job,worker,now):
 with c:
  if c.execute("UPDATE jobs SET status='DONE',lease_owner=NULL,lease_until=NULL,updated_at=? WHERE id=? AND status='LEASED' AND lease_owner=?",(now,job,worker)).rowcount!=1:raise OpsError('cannot complete unowned job')
def fail(c,job,worker,now,error):
 with c:
  row=c.execute('SELECT attempts,max_attempts,irreversible FROM jobs WHERE id=? AND lease_owner=?',(job,worker)).fetchone()
  if not row:raise OpsError('cannot fail unowned job')
  state='DEAD' if row[2] or row[0]>=row[1] else 'RETRY';c.execute('UPDATE jobs SET status=?,last_error=?,lease_owner=NULL,lease_until=NULL,updated_at=? WHERE id=?',(state,error,now,job))
def status(c,job):
 row=c.execute('SELECT status,attempts,max_attempts,lease_owner,lease_until,last_error FROM jobs WHERE id=?',(job,)).fetchone();return dict(zip(('status','attempts','max_attempts','lease_owner','lease_until','last_error'),row)) if row else None
