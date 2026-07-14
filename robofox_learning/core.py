from __future__ import annotations
import hashlib,json,math,re,sqlite3
from pathlib import Path
class LearningError(ValueError):pass
def canon(v):
 try:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
 except Exception as e:raise LearningError(f'noncanonical value: {e}') from e
def digest(v):return 'sha256:'+hashlib.sha256(canon(v).encode()).hexdigest()
def finite(v,name,lo=0,hi=1):
 if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)) or not lo<=float(v)<=hi:raise LearningError(f'{name} must be {lo}..{hi}')
 return float(v)
def exact(r,keys):
 if not isinstance(r,dict) or set(r)!=keys:raise LearningError(f'invalid fields: expected {sorted(keys)}')
def validate_prediction(r):
 keys={'id','product','question','predicted_probability','confidence','made_at','decision_id','experiment_id','evidence_ids','model_version'};exact(r,keys)
 if not re.fullmatch(r'PRD-[A-Z0-9-]{6,80}',r['id']):raise LearningError('invalid prediction id')
 p=finite(r['predicted_probability'],'predicted_probability')
 if r['confidence'] not in {'LOW','MEDIUM','HIGH'}:raise LearningError('invalid confidence')
 if not r['evidence_ids']:raise LearningError('prediction needs evidence')
 return {**r,'predicted_probability':p}
def validate_outcome(r):
 keys={'id','prediction_id','actual','observed_at','source_ids','experiment_family_id','revenue_quality','retention_signal','margin_signal'};exact(r,keys)
 if not re.fullmatch(r'OUT-[A-Z0-9-]{6,80}',r['id']) or not isinstance(r['actual'],bool):raise LearningError('invalid outcome')
 if not r['source_ids']:raise LearningError('outcome needs sources')
 return {**r,'revenue_quality':finite(r['revenue_quality'],'revenue_quality'),'retention_signal':finite(r['retention_signal'],'retention_signal'),'margin_signal':finite(r['margin_signal'],'margin_signal')}
def calibration(predictions,outcomes):
 by={o['prediction_id']:o for o in outcomes};pairs=[(p,by[p['id']]) for p in predictions if p['id'] in by]
 if not pairs:return {'count':0,'brier_score':None,'accuracy':None,'overconfidence':None}
 b=sum((p['predicted_probability']-(1 if o['actual'] else 0))**2 for p,o in pairs)/len(pairs)
 acc=sum((p['predicted_probability']>=.5)==o['actual'] for p,o in pairs)/len(pairs)
 over=sum(max(0,p['predicted_probability']-(1 if o['actual'] else 0)) for p,o in pairs)/len(pairs)
 return {'count':len(pairs),'brier_score':round(b,6),'accuracy':round(acc,6),'overconfidence':round(over,6)}
def belief_update(prior,direction,strength,source_ids,family_ids):
 prior=finite(prior,'prior');strength=finite(strength,'strength')
 if direction not in {'SUPPORT','REFUTE','MIXED'}:raise LearningError('invalid direction')
 if not source_ids:raise LearningError('belief update needs sources')
 independence=max(1,len(set(family_ids)));effective=strength*min(1,independence/3)
 delta={'SUPPORT':.25,'REFUTE':-.25,'MIXED':0}[direction]*effective
 posterior=max(0,min(1,prior+delta))
 return {'prior':prior,'posterior':round(posterior,6),'delta':round(posterior-prior,6),'direction':direction,'effective_strength':round(effective,6),'trigger_phase2':abs(posterior-prior)>=.2}
def benchmark_override(record):
 required={'source_type','sample_size','relevance','product_match','segment_match','offer_version_match','metric','value'};exact(record,required)
 if record['source_type']!='FIRST_PARTY':return {'eligible':False,'reason':'not first-party'}
 if not isinstance(record['sample_size'],int) or record['sample_size']<30:return {'eligible':False,'reason':'sample below 30'}
 if finite(record['relevance'],'relevance')<.7:return {'eligible':False,'reason':'relevance below 0.7'}
 if not all(record[k] for k in ('product_match','segment_match','offer_version_match')):return {'eligible':False,'reason':'context mismatch'}
 return {'eligible':True,'reason':'first-party override gate passed','metric':record['metric'],'value':record['value']}
WEIGHTS={'revenue_quality':.2,'margin':.15,'retention':.15,'attribution_confidence':.1,'learning_value':.1,'conversion_readiness':.1,'founder_efficiency':.1,'cash_efficiency':.05,'trust_safety':.05}
def channel_score(r):
 if set(r)!=set(WEIGHTS):raise LearningError('scorecard fields differ')
 vals={k:finite(v,k) for k,v in r.items()};return round(sum(vals[k]*w for k,w in WEIGHTS.items()),6)
def allocate(channels,total=100,max_share=.5):
 if not channels:raise LearningError('channels required')
 total=float(total);cap=total*finite(max_share,'max_share',.1,1);positive={k:max(0,float(v)) for k,v in channels.items()};s=sum(positive.values())
 if s<=0:raise LearningError('positive scores required')
 alloc={k:min(cap,total*v/s) for k,v in positive.items()};remaining=total-sum(alloc.values())
 while remaining>1e-9:
  eligible=[k for k in alloc if alloc[k]<cap-1e-9]
  if not eligible:break
  add=remaining/len(eligible)
  for k in eligible:
   x=min(add,cap-alloc[k]);alloc[k]+=x;remaining-=x
 return {k:round(v,6) for k,v in sorted(alloc.items())}
def sensitivity(scorecards,variation=.2):
 base=sorted(((channel_score(v),k) for k,v in scorecards.items()),reverse=True);leader=base[0][1];flips=[]
 for channel,values in scorecards.items():
  for field in values:
   changed={k:dict(v) for k,v in scorecards.items()};changed[channel][field]=max(0,min(1,changed[channel][field]*(1+variation)));new=max(changed,key=lambda k:(channel_score(changed[k]),k))
   if new!=leader:flips.append({'changed_channel':channel,'field':field,'new_leader':new})
 return {'base_leader':leader,'rank_flips':flips,'robust':not flips}
def install(c):c.executescript((Path(__file__).resolve().parent/'migrations/001_learning.sql').read_text());c.commit()
def append(c,table,record):
 with c:c.execute(f'INSERT INTO {table}(id,record_json,record_hash) VALUES(?,?,?)',(record['id'],canon(record),digest(record)))
def integrity(c):
 issues=[]
 for table in ('predictions','outcomes','belief_updates','portfolio_recommendations'):
  for row in c.execute(f'SELECT id,record_json,record_hash FROM {table}'):
   if digest(json.loads(row[1]))!=row[2]:issues.append(f'hash mismatch {table}.{row[0]}')
 return {'ok':not issues,'issues':issues}
