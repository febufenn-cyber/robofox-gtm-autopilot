from __future__ import annotations
from .store import add_entity,add_event,add_payment
from .validation import RevenueError,canonical_hash
def ingest_snapshot(c,snapshot:dict)->dict:
 if snapshot.get('mode')!='READ_ONLY':raise RevenueError('ingestion must be READ_ONLY')
 if snapshot.get('source') not in {'HUBSPOT','META','SYNTHETIC'}:raise RevenueError('unsupported ingestion source')
 if not isinstance(snapshot.get('cursor'),str) or not snapshot['cursor']:raise RevenueError('cursor required')
 records=snapshot.get('records')
 if not isinstance(records,list):raise RevenueError('records list required')
 inserted=[];duplicates=[]
 with c:
  for item in records:
   kind=item.get('record_type');record=item.get('record')
   if kind not in {'entity','event','payment'} or not isinstance(record,dict):raise RevenueError('invalid snapshot item')
   try:inserted.append({'entity':add_entity,'event':add_event,'payment':add_payment}[kind](c,record,commit=False))
   except Exception as exc:
    if 'UNIQUE constraint failed' in str(exc):duplicates.append(record.get('id'))
    else:raise
  c.execute('INSERT INTO ingestion_runs(id,source,cursor,record_count,snapshot_hash) VALUES(?,?,?,?,?)',(canonical_hash([snapshot['source'],snapshot['cursor']])[-32:],snapshot['source'],snapshot['cursor'],len(records),canonical_hash(snapshot)))
 return {'inserted':inserted,'duplicates':duplicates,'cursor':snapshot['cursor']}
