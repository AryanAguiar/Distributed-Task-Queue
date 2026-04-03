import re
import httpx
from models import SummarisePayload, ValidatePayload, TranslatePayload, WebhookDeliverPayload, PDFExtractPayload, DataQualityPayload, HealthCheckPayload, ReportGeneratePayload, JOB_PAYLOAD_MAP
from ai import run_ai, execute_ai_prompt
from config import AI_ENABLED
import httpx
import re


async def handle_summarise(payload: SummarisePayload) -> dict:
    prompt = (
        f"Summarise the following text in {payload.max_words} words max. "
        f"Format: {payload.style}.\n\n{payload.text}"
    )
    response_text = await execute_ai_prompt(prompt)
    return {"summary": response_text, "style": payload.style}


async def handle_validate(payload: ValidatePayload) -> dict:
    errors = []

    for rule in payload.rules:
        if rule == "no_nulls":
            nulls = [k for k, v in payload.data.items() if v is None or v == ""]
            if nulls:
                errors.append({"rule": "no_nulls", "fields": nulls})

        elif rule == "email_format":
            email = payload.data.get("email", "")
            if not re.match(r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$", str(email)):
                errors.append({"rule": "email_format", "value": email})

        elif rule == "age_range":
            age = payload.data.get("age")
            if age is not None and not (0 <= int(age) <= 120):
                errors.append({"rule": "age_range", "value": age})

        elif rule == "phone_format":
            phone = payload.data.get("phone", "")
            if not re.match(r"^\+?[\d\s\-()]{7,15}$", str(phone)):
                errors.append({"rule": "phone_format", "value": phone})

    passed = len(errors) == 0
    if payload.strict and not passed:
        raise ValueError(f"Validation failed: {errors}")

    return {"passed": passed, "errors": errors, "checked_rules": payload.rules}


async def handle_translate(payload: TranslatePayload) -> dict:
    prompt = (
        f"Translate the following text to {payload.target_lang}. "
        f"Formality: {payload.formality}. "
        f"Reply with only the translated text, nothing else.\n\n{payload.text}"
    )
    response_text = await execute_ai_prompt(prompt)
    return {
        "translated": response_text,
        "source_lang": payload.source_lang,
        "target_lang": payload.target_lang,
    }


async def handle_webhook_deliver(payload: WebhookDeliverPayload) -> dict:
    async with httpx.AsyncClient(timeout=10) as http:
        response = await http.request(
            method=payload.method,
            url=payload.url,
            json=payload.body,
            headers=payload.headers,
        )
    success = response.status_code not in payload.retry_on
    if not success:
        raise ValueError(f"Webhook got {response.status_code} — will retry")
    return {"status_code": response.status_code, "url": payload.url}


async def handle_data_quality_check(payload: DataQualityPayload) -> dict:
    issues = []
    for i, record in enumerate(payload.records):
        for rule in payload.rules:
            if rule == "no_nulls":
                nulls = [k for k, v in record.items() if v is None or v == ""]
                if nulls:
                    issues.append({"record": i, "rule": rule, "fields": nulls})
            elif rule == "email_format":
                email = record.get("email", "")
                if not re.match(r"^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$", str(email)):
                    issues.append({"record": i, "rule": rule, "value": email})
            elif rule == "age_range":
                age = record.get("age")
                if age is not None and not (0 <= int(age) <= 120):
                    issues.append({"record": i, "rule": rule, "value": age})

    return {
        "total_records": len(payload.records),
        "issues_found": len(issues),
        "passed": len(issues) == 0,
        "issues": issues,
    }


async def handle_health_check_batch(payload: HealthCheckPayload) -> dict:
    results = []
    async with httpx.AsyncClient(timeout=payload.timeout_seconds) as http:
        for url in payload.urls:
            try:
                r = await http.get(url)
                results.append({
                    "url": url,
                    "status": r.status_code,
                    "ok": r.status_code == payload.expected_status,
                    "latency_ms": int(r.elapsed.total_seconds() * 1000),
                })
            except Exception as e:
                results.append({"url": url, "status": None, "ok": False, "error": str(e)})

    return {
        "checked": len(results),
        "healthy": sum(1 for r in results if r["ok"]),
        "results": results,
    }


async def handle_report_generate(payload: ReportGeneratePayload) -> dict:
    prompt = (
        f"Generate a structured report titled '{payload.title}'. "
        f"Include these sections: {', '.join(payload.sections)}. "
        f"Be concise and professional."
    )
    response_text = await execute_ai_prompt(prompt)
    return {
        "title": payload.title,
        "format": payload.format,
        "content": response_text,
        "sections": payload.sections,
    }


JOB_HANDLERS = {
    "summarise": handle_summarise,
    "validate": handle_validate,
    "translate": handle_translate,
    "webhook_deliver": handle_webhook_deliver,
    "data_quality_check": handle_data_quality_check,
    "health_check_batch": handle_health_check_batch,
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
