from datetime import datetime

def create_log(db, actor, action, resource_type, resource_id, details, severity="info"):
    log = {
        "timestamp": datetime.utcnow(),
        "actor": actor,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details,
        "severity": severity
    }

    db.audit_logs.insert_one(log)