from ai import run_ai
from config import AI_ENABLED
from app.schemas import JOB_PAYLOAD_MAP

from app.handlers.report import (
    handle_summarise, handle_validate, handle_translate, 
    handle_webhook_deliver, handle_data_quality_check, handle_report_generate
)
from app.handlers.health_check import handle_health_check, handle_health_check_batch
from app.handlers.incident import handle_incident_open, handle_incident_resolve
from app.handlers.alert import handle_alert_dispatch
from app.handlers.escalation import handle_escalation_check

JOB_HANDLERS = {
    "summarise": handle_summarise,
    "validate": handle_validate,
    "translate": handle_translate,
    "webhook_deliver": handle_webhook_deliver,
    "data_quality_check": handle_data_quality_check,
    "health_check": handle_health_check,
    "health_check_batch": handle_health_check_batch,
    "incident_open": handle_incident_open,
    "alert_dispatch": handle_alert_dispatch,
    "escalation_check": handle_escalation_check,
    "incident_resolve": handle_incident_resolve,
    "report_generate": handle_report_generate,
}

async def process_job_payload(job_type: str, payload: dict, use_ai: bool = False) -> str:
    if not use_ai and job_type in ["summarise", "translate", "report_generate"]:
        raise ValueError(f"Task '{job_type}' strictly requires AI to be enabled. Pass use_ai=True.")

    if AI_ENABLED and use_ai:
        return await run_ai(job_type, payload)

    handler = JOB_HANDLERS.get(job_type)
    if handler:
        payload_class = JOB_PAYLOAD_MAP.get(job_type)
        if payload_class:
            try:
                parsed_payload = payload_class(**payload)
            except Exception as e:
                return f"Validation error: {e}"
        else:
            parsed_payload = payload
            
        return await handler(parsed_payload)
    else:
        return f"Unknown job type: {job_type}"
