from __future__ import annotations
from .validation import validate_qualification
def qualify(features:dict)->dict:
 f=validate_qualification(features)
 if f['consent_status'] in {'OPTED_OUT','DO_NOT_CONTACT'}:return {'status':'DISQUALIFIED','score':0,'reasons':['contact restricted'],'confidence':'HIGH'}
 weights={'segment_match':2,'pain_signal':3,'authority_signal':2,'urgency_signal':2,'budget_signal':1}
 score=sum(w for k,w in weights.items() if f.get(k) is True);known=sum(1 for k in weights if f.get(k) is not None)
 status='QUALIFIED' if score>=7 and f['consent_status'] in {'OPTED_IN','EXISTING_RELATIONSHIP'} else 'REVIEW' if score>=4 else 'DISQUALIFIED'
 reasons=[k for k in weights if f.get(k) is True]
 return {'status':status,'score':score,'reasons':reasons,'confidence':'HIGH' if known==5 else 'MEDIUM' if known>=3 else 'LOW'}
