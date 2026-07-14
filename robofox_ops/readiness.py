from __future__ import annotations

def validate_environment(config):
 if config.get('environment') not in {'development','staging','production'}:return ['invalid environment']
 errors=[]
 if config['environment']=='production' and config.get('autonomous_deploy'):errors.append('production deployment cannot be autonomous')
 if config.get('environment')=='production' and 'test' in config.get('workspace','').lower():errors.append('production points to test workspace')
 if config.get('environment')!='production' and 'prod' in config.get('workspace','').lower():errors.append('non-production points to production workspace')
 return errors

def readiness_report(checks):
 required={'rbac','secret_redaction','queue_deduplication','backup_restore','staging_rollback','incident_runbooks','phase0_7_gate'}
 missing=sorted(required-set(checks));failed=sorted(k for k in required if not checks.get(k))
 return {'v1_ready':not missing and not failed,'missing':missing,'failed':failed,'phase8_ready':False,'phase8_reason':'requires two validated products and observed shared-resource conflicts'}
