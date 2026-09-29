import json
import os
import time
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq
from hindsight_client import Hindsight
from pydantic import BaseModel, Field


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

APP_VERSION = "3.0.0"

HINDSIGHT_URL = os.getenv(
    "HINDSIGHT_URL",
    "https://api.hindsight.vectorize.io"
).rstrip("/")

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")

BANK_ID = os.getenv(
    "HINDSIGHT_BANK_ID",
    "nexus-demo-v2"
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)


# ============================================================
# CORS
# ============================================================

ALLOWED_ORIGINS = [
    "https://nexus-three-delta-57.vercel.app",
    "http://localhost:5173",
]

# Also allow additional origins from Render environment variables.
extra_origins = os.getenv("ALLOWED_ORIGINS", "")

if extra_origins:
    ALLOWED_ORIGINS.extend(
        origin.strip()
        for origin in extra_origins.split(",")
        if origin.strip()
    )

# Remove duplicates while preserving order.
ALLOWED_ORIGINS = list(dict.fromkeys(ALLOWED_ORIGINS))


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="NEXUS — Organizational Memory",
    version=APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CLIENTS
# ============================================================

hindsight = (
    Hindsight(
        base_url=HINDSIGHT_URL,
        api_key=HINDSIGHT_API_KEY
    )
    if HINDSIGHT_API_KEY
    else None
)

groq = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY
    else None
)

startup_state = {
    "hindsight": False,
    "seeded": False,
    "error": None
}


# ============================================================
# SEED EXPERIENCES
# ============================================================

SEED_EXPERIENCES = [
    {
        "id": "INC-184",
        "content": (
            "Incident INC-184: Acme Retail checkout API returned HTTP 503 "
            "because database connection utilization reached 96% and the "
            "connection pool was exhausted. Increasing request timeouts "
            "FAILED and increased queueing. A generic cache-clear workaround "
            "also FAILED. Reducing the DB connection pool from 100 to 60 "
            "and restarting checkout workers SUCCESSFULLY restored service. "
            "Acme Retail was proactively informed; there was no escalation "
            "and the renewal remained on track."
        ),
        "tags": [
            "incident",
            "technical",
            "acme",
            "success",
            "customer"
        ]
    },
    {
        "id": "INC-161",
        "content": (
            "Incident INC-161: Checkout API latency increased during a "
            "traffic spike. Increasing the request timeout FAILED and caused "
            "additional queueing. Scaling checkout workers and reducing "
            "database concurrency SUCCESSFULLY restored service. Proactive "
            "customer communication kept Acme Retail satisfied."
        ),
        "tags": [
            "incident",
            "technical",
            "failed-approach",
            "success"
        ]
    },
    {
        "id": "TKT-902",
        "content": (
            "Support ticket TKT-902: Acme Retail reported intermittent "
            "payment failures. Generic cache clearing FAILED. Reducing "
            "database connection pressure and restarting workers SUCCESSFULLY "
            "resolved the problem. The account manager was notified because "
            "the customer was in a renewal window."
        ),
        "tags": [
            "support",
            "customer",
            "success",
            "renewal"
        ]
    },
    {
        "id": "DEAL-77",
        "content": (
            "Sales experience DEAL-77: Acme Retail places high importance "
            "on payment reliability. During renewal discussions, proactive "
            "incident communication reduced escalation risk. Delayed "
            "communication previously caused customer frustration."
        ),
        "tags": [
            "sales",
            "customer",
            "renewal",
            "business-outcome"
        ]
    },
    {
        "id": "INC-143",
        "content": (
            "Incident INC-143: Payment gateway errors were initially "
            "attributed to an external provider. That hypothesis FAILED. "
            "Investigation showed internal database connection exhaustion. "
            "Checking connection utilization led to the correct diagnosis."
        ),
        "tags": [
            "incident",
            "diagnosis",
            "failed-approach"
        ]
    },
]


# ============================================================
# REQUEST MODELS
# ============================================================

class Incident(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    customer: str = Field(default="Acme Retail", max_length=160)
    severity: str = Field(default="High", max_length=30)
    symptoms: str = Field(min_length=5, max_length=4000)
    context: str = Field(default="", max_length=4000)


class Outcome(BaseModel):
    incident_title: str = Field(min_length=3, max_length=240)
    customer: str = Field(min_length=1, max_length=160)
    resolution: str = Field(min_length=3, max_length=4000)
    result: str = Field(min_length=3, max_length=4000)
    business_outcome: str = Field(default="", max_length=4000)
    successful: bool = True


# ============================================================
# HINDSIGHT HELPERS
# ============================================================

def obj_to_dict(item: Any) -> dict:
    if isinstance(item, dict):
        return item

    for method in ("model_dump", "dict", "to_dict"):
        fn = getattr(item, method, None)

        if callable(fn):
            try:
                return fn()
            except Exception:
                pass

    return {}


def memory_text(item: Any) -> str:
    data = obj_to_dict(item)

    value = data.get("text") or data.get("content")

    if isinstance(value, dict):
        value = value.get("text") or value.get("value")

    if value:
        return str(value)

    value = (
        getattr(item, "text", None)
        or getattr(item, "content", None)
    )

    return str(value) if value else ""


def memory_type(item: Any) -> str:
    data = obj_to_dict(item)

    return str(
        data.get("type")
        or getattr(item, "type", None)
        or "memory"
    )


def memory_context(item: Any) -> str:
    data = obj_to_dict(item)

    return str(
        data.get("context")
        or getattr(item, "context", None)
        or ""
    )


def memory_document(item: Any) -> str:
    data = obj_to_dict(item)

    return str(
        data.get("document_id")
        or data.get("documentId")
        or getattr(item, "document_id", None)
        or ""
    )


def unique_memories(
    items: list[Any],
    limit: int = 8
) -> list[dict]:

    seen = set()
    output = []

    for item in items or []:
        text = memory_text(item).strip()

        key = " ".join(
            text.lower().split()
        )

        if not text or key in seen:
            continue

        seen.add(key)

        output.append(
            {
                "type": memory_type(item),
                "text": text,
                "context": memory_context(item),
                "document_id": memory_document(item)
            }
        )

        if len(output) >= limit:
            break

    return output


# ============================================================
# HINDSIGHT BANK
# ============================================================

async def ensure_bank() -> tuple[bool, str]:

    if not hindsight:
        return False, "HINDSIGHT_API_KEY is missing"

    try:
        await hindsight.acreate_bank(
            bank_id=BANK_ID,
            name="NEXUS Organizational Memory",
            reflect_mission=(
                "Connect technical incidents, support history, customer "
                "context, sales/renewal context and business outcomes. "
                "Prefer documented successful experience and explicitly "
                "avoid approaches documented as failures."
            ),
            retain_mission=(
                "Extract durable technical decisions, failed approaches, "
                "successful resolutions, customer context and measurable "
                "business outcomes."
            ),
            background=(
                "Shared organizational memory for enterprise incidents, "
                "support, sales and operations."
            ),
            enable_observations=True,
        )

        return True, "ready"

    except Exception as exc:
        text = str(exc)

        if "409" in text or "already exists" in text.lower():
            return True, "ready"

        return False, text


async def list_memories(limit=100):

    if not hindsight:
        return []

    response = await hindsight.alist_memories(
        bank_id=BANK_ID,
        limit=limit
    )

    data = obj_to_dict(response)

    items = data.get("items")

    if items is None:
        items = getattr(response, "items", None)

    return list(items or [])


async def seed_if_empty():

    existing = await list_memories(10)

    if existing:
        return False

    for exp in SEED_EXPERIENCES:

        await hindsight.aretain(
            bank_id=BANK_ID,
            content=exp["content"],
            context=(
                f"NEXUS synthetic enterprise experience "
                f"{exp['id']}"
            ),
            document_id=exp["id"],
            tags=exp["tags"],
        )

    return True


async def recall_experiences(
    query: str
) -> tuple[list[dict], Optional[str]]:

    if not hindsight:
        return [], "Hindsight is not configured"

    ok, status = await ensure_bank()

    if not ok:
        return [], status

    errors = []

    queries = [
        query,
        (
            "Relevant Acme Retail incident, support, customer renewal, "
            "successful resolution and failed approach experience related "
            "to database pressure, checkout latency, payment failures "
            "and HTTP 503."
        ),
    ]

    for q in queries:

        try:

            response = await hindsight.arecall(
                bank_id=BANK_ID,
                query=q,
                budget="mid",
                max_tokens=5000,
                types=[
                    "experience",
                    "observation",
                    "world"
                ],
                prefer_observations=True,
            )

            data = obj_to_dict(response)

            raw = data.get("results")

            if raw is None:
                raw = getattr(response, "results", None)

            found = unique_memories(
                list(raw or []),
                limit=8
            )

            if found:
                return found, None

        except Exception as exc:
            errors.append(str(exc))

    return [], errors[-1] if errors else None


# ============================================================
# REQUEST TIMER / ERROR MIDDLEWARE
# ============================================================

@app.middleware("http")
async def request_timer(
    request: Request,
    call_next
):

    started = time.perf_counter()

    try:
        response = await call_next(request)

    except Exception as exc:

        print(
            f"[NEXUS] Unhandled error on "
            f"{request.method} {request.url.path}: {exc}"
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error"
            }
        )

    response.headers["X-NEXUS-Version"] = APP_VERSION

    response.headers["X-Response-Time-ms"] = str(
        round(
            (time.perf_counter() - started) * 1000,
            1
        )
    )

    return response


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup():

    print("\n" + "=" * 62)
    print("NEXUS — ORGANIZATIONAL MEMORY")
    print("=" * 62)

    if not hindsight:

        startup_state["error"] = (
            "HINDSIGHT_API_KEY is missing"
        )

        print(
            "[NEXUS] ERROR: "
            "HINDSIGHT_API_KEY is missing"
        )

        return

    ok, status = await ensure_bank()

    startup_state["hindsight"] = ok

    if not ok:

        startup_state["error"] = status

        print(
            f"[NEXUS] Hindsight setup failed: {status}"
        )

        return

    try:

        startup_state["seeded"] = await seed_if_empty()

        print(
            f"[NEXUS] Hindsight bank "
            f"'{BANK_ID}': ready"
        )

        print(
            f"[NEXUS] Seeded demo experiences: "
            f"{startup_state['seeded']}"
        )

    except Exception as exc:

        startup_state["error"] = str(exc)

        print(
            f"[NEXUS] Seed failed: {exc}"
        )

    print(
        f"[NEXUS] Groq: "
        f"{'ONLINE' if groq else 'NOT CONFIGURED'}"
    )

    print("[NEXUS] Backend ready\n")


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "name": "NEXUS",
        "status": "online",
        "version": APP_VERSION,
        "bank": BANK_ID
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
async def health():

    ok, status = (
        await ensure_bank()
        if hindsight
        else (False, "not configured")
    )

    return {
        "ok": bool(hindsight and ok),
        "version": APP_VERSION,
        "hindsight": bool(hindsight),
        "hindsight_bank": ok,
        "hindsight_bank_status": status,
        "groq": bool(groq),
        "bank_id": BANK_ID
    }


# ============================================================
# EXPERIENCE LIBRARY
# ============================================================

@app.get("/api/experiences")
async def experiences():

    if not hindsight:
        raise HTTPException(
            status_code=503,
            detail="Hindsight is not configured"
        )

    ok, status = await ensure_bank()

    if not ok:
        raise HTTPException(
            status_code=503,
            detail=status
        )

    try:

        items = await list_memories(100)

        clean = unique_memories(
            items,
            limit=40
        )

        return {
            "experiences": clean,
            "count": len(clean),
            "source": "hindsight"
        }

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                f"Could not read Hindsight memory: {exc}"
            )
        )


# ============================================================
# ANALYZE INCIDENT
# ============================================================

@app.post("/api/analyze")
async def analyze(
    incident: Incident
):

    query = f"""
CURRENT INCIDENT
Title: {incident.title}
Customer: {incident.customer}
Severity: {incident.severity}
Symptoms: {incident.symptoms}
Business context: {incident.context}

Find relevant organizational experience.
Prioritize similar technical incidents, successful and failed
approaches, support experiences, customer and renewal context,
and business outcomes.

The goal is to make the next decision better because NEXUS
remembers what happened before.
"""

    memories, recall_error = await recall_experiences(
        query
    )

    memory_block = "\n".join(
        f"- [{m['type']}] {m['text']}"
        for m in memories
    ) or "No previous experience was recalled."

    system = """
You are NEXUS, an enterprise organizational-memory agent.

Your value is using remembered experience, not generic advice.

Use recalled evidence explicitly.

If memory says an approach FAILED, do not recommend it
as the primary fix.

If memory says an approach SUCCEEDED, consider it strongly
when the pattern matches.

Connect technical outcome to customer/business outcome
when relevant.

Never claim an action happened unless it is in memory or
the current incident.

Return ONLY valid JSON with keys:

summary,
recommendation,
why,
avoid,
customer_context,
confidence,
learning.
"""

    prompt = (
        f"{query}\n\n"
        f"RECALLED HINDSIGHT EXPERIENCE\n"
        f"{memory_block}\n\n"
        f"Produce the next decision."
    )

    decision = None
    llm_error = None

    if groq:

        try:

            response = groq.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0.15,
                response_format={
                    "type": "json_object"
                },
                messages=[
                    {
                        "role": "system",
                        "content": system
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )

            decision = json.loads(
                response.choices[0].message.content
            )

        except Exception as exc:

            llm_error = str(exc)

            print(
                f"[NEXUS] Groq error: {exc}"
            )

    if not decision:

        decision = {
            "summary": (
                "NEXUS found a strong "
                "database-saturation pattern "
                "in prior experience."
            ),
            "recommendation": (
                "Reduce database connection pressure, "
                "restart checkout workers, then verify "
                "recovery before scaling further."
            ),
            "why": (
                "Prior Acme incidents show that reducing "
                "DB pressure and restarting workers "
                "succeeded, while increasing timeouts "
                "and generic cache clearing failed."
            ),
            "avoid": (
                "Do not increase request timeouts as "
                "the primary fix; avoid generic cache "
                "clearing and delayed customer communication."
            ),
            "customer_context": (
                "Acme Retail is an enterprise customer "
                "in an active renewal window. Proactive "
                "communication was successful previously."
            ),
            "confidence": 0.90,
            "learning": (
                "After resolution, retain the root cause, "
                "action, technical result and "
                "customer/business outcome."
            ),
        }

    try:

        confidence = float(
            decision.get("confidence", 0.9)
        )

        if confidence > 1:
            confidence /= 100

        decision["confidence"] = round(
            max(0, min(confidence, 1)),
            2
        )

    except Exception:

        decision["confidence"] = 0.9

    return {
        "incident": incident.model_dump(),
        "memories": memories,
        "memory_count": len(memories),
        "memory_status": (
            "recalled"
            if memories
            else (
                "unavailable"
                if recall_error
                else "empty"
            )
        ),
        "memory_error": recall_error,
        "llm_status": (
            "groq"
            if groq and not llm_error
            else "fallback"
        ),
        "decision": decision,
    }


# ============================================================
# LEARN / RETAIN OUTCOME
# ============================================================

@app.post("/api/learn")
async def learn(
    outcome: Outcome
):

    if not hindsight:
        raise HTTPException(
            status_code=503,
            detail="Hindsight is not configured"
        )

    ok, status = await ensure_bank()

    if not ok:
        raise HTTPException(
            status_code=503,
            detail=status
        )

    content = f"""
NEXUS OUTCOME — REUSABLE ORGANIZATIONAL EXPERIENCE

Incident: {outcome.incident_title}
Customer: {outcome.customer}
Resolution: {outcome.resolution}
Technical result: {outcome.result}
Business/customer outcome: {outcome.business_outcome}
Successful: {outcome.successful}

This is the observed outcome of a NEXUS decision cycle.
Future similar incidents should use this experience.
"""

    try:

        response = await hindsight.aretain(
            bank_id=BANK_ID,
            content=content,
            context="NEXUS decision outcome learning",
            document_id=f"OUTCOME-{int(time.time())}",
            tags=[
                "outcome",
                "learned-experience",
                "nexus"
            ],
        )

        return {
            "stored": True,
            "message": (
                "Experience retained in Hindsight."
            ),
            "id": obj_to_dict(response).get("id")
        }

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                f"Hindsight retain failed: {exc}"
            )
        )
