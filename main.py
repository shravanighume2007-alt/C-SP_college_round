from __future__ import annotations

"""BLACKOUT backend: FastAPI + deterministic rule-based agent + JSON persistence.

Run:  uvicorn main:app --reload --port 8000
State is persisted to ``nexus_db.json`` in this directory (atomic writes).
"""


import json
import os
import re
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).resolve().parent / "nexus_db.json"
DB_LOCK = threading.RLock()

ModuleName = Literal["website", "crm", "marketing", "billing", "approval"]

# --------------------------------------------------------------------------- #
# Pydantic models
# --------------------------------------------------------------------------- #


class ParseRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1000)


class WebsiteSpec(BaseModel):
    slug: str
    title: str
    headline: str
    subheadline: str
    sections: List[str]
    theme: str = "tokyo-nights"


class SegmentSpec(BaseModel):
    name: str
    criteria: str
    threshold: float
    lead_ids: List[str]
    lead_count: int
    total_value: float


class BillingSpec(BaseModel):
    plan_name: str
    price: float
    interval_days: int
    currency: str = "USD"
    subscriber_ids: List[str]
    projected_mrr: float


class CampaignSpec(BaseModel):
    name: str
    channel: str
    audience_size: int
    scheduled_for: str


class Entities(BaseModel):
    topic: str
    website: Optional[WebsiteSpec] = None
    segment: Optional[SegmentSpec] = None
    billing: Optional[BillingSpec] = None
    campaign: Optional[CampaignSpec] = None


class PlanStep(BaseModel):
    id: str
    module: ModuleName
    title: str
    detail: str
    duration_ms: int
    requires_approval: bool = False
    logs: List[str] = Field(default_factory=list)
    chips: List[str] = Field(default_factory=list)


class ApprovalSpec(BaseModel):
    title: str
    message: str
    sensitive_actions: List[str]
    impact: Dict[str, float]


class ExecutionPlan(BaseModel):
    plan_id: str
    prompt: str
    summary: str
    steps: List[PlanStep]
    entities: Entities
    approval: ApprovalSpec
    created_at: str


class ExecutedStep(PlanStep):
    status: Literal["completed"] = "completed"
    started_at: str
    completed_at: str


class ApproveRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1000)
    plan: ExecutionPlan
    approved_by: str = "operator"


class ApproveResponse(BaseModel):
    status: Literal["committed", "already_committed"]
    workflow_id: str
    request_id: str
    committed_at: str
    summary: Dict[str, Any]
    executed_steps: List[ExecutedStep]


# --------------------------------------------------------------------------- #
# Persistence helpers
# --------------------------------------------------------------------------- #


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime, precision: str = "seconds") -> str:
    return dt.isoformat(timespec=precision).replace("+00:00", "Z")


def read_db() -> Dict[str, Any]:
    try:
        with DB_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="nexus_db.json not found in backend root") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"nexus_db.json is corrupted: {exc}") from exc


def write_db(db: Dict[str, Any]) -> None:
    """Atomic write: temp file in the same directory, fsync, then os.replace."""
    fd, tmp_path = tempfile.mkstemp(dir=str(DB_PATH.parent), prefix=".nexus_db.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(db, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, DB_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# --------------------------------------------------------------------------- #
# Deterministic rule-based agent
# --------------------------------------------------------------------------- #

INTENTS: Dict[str, "re.Pattern[str]"] = {
    "website": re.compile(r"\b(website|web site|site|landing|page|promo|microsite)\b"),
    "crm": re.compile(r"\b(crm|leads?|segment|filter|customers?|prospects?|contacts?)\b"),
    "marketing": re.compile(
        r"\b(emails?|campaigns?|newsletter|announce|announcement|outreach|blast|promote|marketing)\b"
    ),
    "billing": re.compile(
        r"\b(billing|subscriptions?|recurring|invoice|plan|payments?|pricing|charge)\b"
    ),
}
BILLING_CLAUSE = INTENTS["billing"]
HIGH_VALUE_RE = re.compile(r"high[\s-]?value|top\s+leads?|\bvip\b|premium\s+leads?|big\s+spenders?")
THRESHOLD_RE = re.compile(
    r"(?:over|above|more than|greater than|exceeding|at least|>=?)\s*\$?\s*(\d[\d,]*(?:\.\d+)?)\s*(k|m)?",
    re.IGNORECASE,
)
TOPIC_RE = re.compile(
    r"\b(?:for|about|promoting|promote)\s+(?:our|the|my|a|an)?\s*(?:upcoming|new|latest|next)?\s*"
    r"([a-z0-9&\- ]{1,40}?)\s+(webinar|event|launch|workshop|product|masterclass|conference)\b",
    re.IGNORECASE,
)
PRICE_RE = re.compile(r"(?:[$€₹]\s?(\d[\d,]*(?:\.\d+)?))|(?:(\d[\d,]*(?:\.\d+)?)\s*(?:dollars|usd|bucks))", re.IGNORECASE)
INTERVAL_RE = re.compile(r"(\d+)\s*-?\s*day", re.IGNORECASE)
ACRONYMS = {"ai", "ml", "saas", "crm", "api", "ui", "ux", "b2b", "b2c"}
EXCLUDED_STATUSES = {"Cold", "Lost", "Won"}
DEFAULT_PRICE = 149.0
HIGH_VALUE_THRESHOLD = 10_000.0
WARM_THRESHOLD = 5_000.0


def title_case(text: str) -> str:
    return " ".join(w.upper() if w.lower() in ACRONYMS else w.capitalize() for w in text.split())


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "site"


def parse_topic(text: str) -> str:
    match = TOPIC_RE.search(text)
    if match:
        return title_case(f"{match.group(1).strip()} {match.group(2)}")
    if "webinar" in text.lower():
        return "Webinar"
    return "Business Launch"


def parse_threshold(text: str, low: str) -> float:
    match = THRESHOLD_RE.search(text)
    if match:
        amount = float(match.group(1).replace(",", ""))
        suffix = (match.group(2) or "").lower()
        return amount * {"k": 1_000, "m": 1_000_000}.get(suffix, 1)
    return HIGH_VALUE_THRESHOLD if HIGH_VALUE_RE.search(low) else WARM_THRESHOLD


def parse_billing_terms(text: str) -> Dict[str, float]:
    """Read price + interval only from clauses that talk about billing."""
    clauses = [c for c in re.split(r"[,;.]|\bthen\b", text, flags=re.IGNORECASE) if BILLING_CLAUSE.search(c.lower())]
    scope = THRESHOLD_RE.sub(" ", " ".join(clauses) if clauses else text)
    low = scope.lower()
    price = DEFAULT_PRICE
    price_match = PRICE_RE.search(scope)
    if price_match:
        price = float((price_match.group(1) or price_match.group(2)).replace(",", ""))
    interval = 30
    interval_match = INTERVAL_RE.search(scope)
    if interval_match:
        interval = max(1, int(interval_match.group(1)))
    elif "weekly" in low:
        interval = 7
    elif "quarterly" in low:
        interval = 90
    elif "yearly" in low or "annual" in low:
        interval = 365
    return {"price": price, "interval_days": float(interval)}


def money(value: float) -> str:
    return f"${value:,.0f}"


def build_plan(prompt: str, db: Dict[str, Any]) -> ExecutionPlan:
    text = " ".join(prompt.split())
    low = text.lower()
    wants = {name: bool(rx.search(low)) for name, rx in INTENTS.items()}
    fallback = not any(wants.values())
    if fallback:
        wants["crm"] = True

    topic = parse_topic(text)
    leads: List[Dict[str, Any]] = db.get("leads", [])
    now = now_utc()

    # --- CRM segmentation -------------------------------------------------- #
    segment: Optional[SegmentSpec] = None
    if wants["crm"]:
        threshold = parse_threshold(text, low)
        eligible = sorted(
            (l for l in leads if l["status"] not in EXCLUDED_STATUSES and l["value"] >= threshold),
            key=lambda l: l["value"],
            reverse=True,
        )
        label = "High-Value Leads" if threshold >= HIGH_VALUE_THRESHOLD else "Warm Leads"
        segment = SegmentSpec(
            name=f"{label} (≥ {money(threshold)})",
            criteria=f"deal value ≥ {money(threshold)} AND status not in {sorted(EXCLUDED_STATUSES)}",
            threshold=threshold,
            lead_ids=[l["id"] for l in eligible],
            lead_count=len(eligible),
            total_value=float(sum(l["value"] for l in eligible)),
        )

    # Audience shared by marketing/billing when no explicit segment was requested.
    if segment:
        audience_ids = segment.lead_ids
    else:
        audience_ids = [l["id"] for l in leads if l["status"] in {"Qualified", "Negotiating"}]
    audience = len(audience_ids)

    # --- Website ------------------------------------------------------------ #
    website: Optional[WebsiteSpec] = None
    if wants["website"]:
        website = WebsiteSpec(
            slug=f"{slugify(topic)}-promo",
            title=f"{topic} | BLACKOUT",
            headline=f"Join the {topic}",
            subheadline="Reserve your seat. Limited spots, live Q&A, and an exclusive offer for attendees.",
            sections=["Hero", "Agenda", "Speakers", "Live Registration Form", "FAQ"],
        )

    # --- Marketing ----------------------------------------------------------- #
    campaign: Optional[CampaignSpec] = None
    if wants["marketing"]:
        campaign = CampaignSpec(
            name=f"{topic} Announcement",
            channel="Email",
            audience_size=audience,
            scheduled_for=iso(now + timedelta(days=1), "seconds"),
        )

    # --- Billing -------------------------------------------------------------- #
    billing: Optional[BillingSpec] = None
    if wants["billing"]:
        terms = parse_billing_terms(text)
        price, interval = terms["price"], int(terms["interval_days"])
        billing = BillingSpec(
            plan_name=f"{topic} VIP {interval}-Day Plan",
            price=price,
            interval_days=interval,
            subscriber_ids=audience_ids,
            projected_mrr=round(price * audience * 30 / interval, 2),
        )

    # --- Steps ------------------------------------------------------------------ #
    steps: List[PlanStep] = []

    def add(module: ModuleName, title: str, detail: str, ms: int, logs: List[str], chips: List[str], gate: bool = False) -> None:
        steps.append(
            PlanStep(
                id=f"step-{len(steps) + 1}",
                module=module,
                title=title,
                detail=detail,
                duration_ms=ms,
                requires_approval=gate,
                logs=logs,
                chips=chips,
            )
        )

    if website:
        add(
            "website",
            "Website Generation",
            f"Scaffolding responsive promo site for the {topic}.",
            1900,
            [
                f"> init page '{website.slug}' with theme {website.theme}",
                f"> compose sections: {', '.join(website.sections)}",
                "> wire registration form to CRM intake",
            ],
            [f"/{website.slug}", f"{len(website.sections)} sections", "responsive"],
        )
    if segment:
        add(
            "crm",
            "CRM List Segmentation",
            f"Filtering {len(leads)} CRM records with: {segment.criteria}.",
            1700,
            [
                f"> scan {len(leads)} records",
                f"> rule: {segment.criteria}",
                f"> matched {segment.lead_count} leads worth {money(segment.total_value)}",
            ],
            [f"{segment.lead_count} leads", money(segment.total_value) + " pipeline"],
        )
    if campaign:
        add(
            "marketing",
            "Campaign Scheduling",
            f"Drafting '{campaign.name}' for {campaign.audience_size} contacts.",
            1500,
            [
                f"> render {campaign.channel.lower()} template",
                f"> audience resolved: {campaign.audience_size} contacts",
                f"> schedule send for {campaign.scheduled_for}",
            ],
            [campaign.channel, f"{campaign.audience_size} recipients"],
        )
    if billing:
        add(
            "billing",
            "Billing Strategy Set",
            f"Configuring {money(billing.price)} every {billing.interval_days} days for {audience} leads.",
            1800,
            [
                f"> create plan '{billing.plan_name}'",
                f"> cadence: every {billing.interval_days} days, auto-renew",
                f"> projected MRR impact: {money(billing.projected_mrr)}",
            ],
            [f"{money(billing.price)} / {billing.interval_days}d", f"+{money(billing.projected_mrr)} MRR"],
        )

    sensitive: List[str] = []
    if website:
        sensitive.append(f"Publish '/{website.slug}' to the public web")
    if campaign:
        sensitive.append(f"Send '{campaign.name}' to {campaign.audience_size} contacts")
    if billing:
        sensitive.append(
            f"Enroll {audience} leads in recurring billing ({money(billing.price)} every {billing.interval_days} days)"
        )
    if segment:
        sensitive.append(f"Tag {segment.lead_count} CRM records with segment '{segment.name}'")
    sensitive.append("Persist workflow, requests and analytics to nexus_db.json")

    impact: Dict[str, float] = {
        "leads_affected": float(len(audience_ids)),
        "pipeline_value": float(segment.total_value if segment else sum(l["value"] for l in leads if l["id"] in audience_ids)),
        "projected_mrr": float(billing.projected_mrr if billing else 0),
    }
    approval = ApprovalSpec(
        title="Authorization Required",
        message="The agent prepared sensitive operations that change live data. Review and authorize before anything is committed.",
        sensitive_actions=sensitive,
        impact=impact,
    )
    add(
        "approval",
        "Approval Gate",
        "Execution paused. Sensitive operations require explicit human authorization.",
        900,
        ["> policy check: destructive/financial actions detected", "> awaiting operator decision"],
        [f"{len(sensitive)} sensitive actions"],
        gate=True,
    )

    modules = [s.module for s in steps if s.module != "approval"]
    summary = (
        f"Interpreted as {len(modules)} module action(s): {', '.join(modules)}, then an approval gate."
        if not fallback
        else "No explicit module keywords found, so the agent defaulted to CRM lead segmentation, then an approval gate."
    )

    return ExecutionPlan(
        plan_id=f"plan-{uuid4().hex[:10]}",
        prompt=text,
        summary=summary,
        steps=steps,
        entities=Entities(topic=topic, website=website, segment=segment, billing=billing, campaign=campaign),
        approval=approval,
        created_at=iso(now),
    )


# --------------------------------------------------------------------------- #
# Commit logic
# --------------------------------------------------------------------------- #


def unique_slug(db: Dict[str, Any], slug: str) -> str:
    taken: Set[str] = {w["slug"] for w in db.get("websites", [])}
    if slug not in taken:
        return slug
    n = 2
    while f"{slug}-{n}" in taken:
        n += 1
    return f"{slug}-{n}"


def dashboard_payload(db: Dict[str, Any]) -> Dict[str, Any]:
    plans = db.get("subscription_plans", [])
    leads = db.get("leads", [])
    mrr = sum(p["price"] * p["subscribers"] * 30 / max(p["interval_days"], 1) for p in plans)
    kpis = {
        "total_leads": len(leads),
        "pipeline_value": sum(l["value"] for l in leads),
        "active_subscribers": sum(p["subscribers"] for p in plans),
        "mrr": round(mrr, 2),
        "workflows_completed": len(db.get("workflows", [])),
        "websites_live": len(db.get("websites", [])),
        "segmented_leads": sum(1 for l in leads if l.get("segment")),
    }
    return {**db, "kpis": kpis}


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #

app = FastAPI(title="BLACKOUT API", version="1.0.0")
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "db": str(DB_PATH.name)}


@app.get("/api/dashboard")
def get_dashboard() -> Dict[str, Any]:
    with DB_LOCK:
        return dashboard_payload(read_db())


@app.post("/api/agent/parse", response_model=ExecutionPlan)
def parse_command(body: ParseRequest) -> ExecutionPlan:
    with DB_LOCK:
        db = read_db()
    return build_plan(body.prompt, db)


@app.post("/api/agent/approve", response_model=ApproveResponse)
def approve_plan(body: ApproveRequest) -> ApproveResponse:
    plan = body.plan
    with DB_LOCK:
        db = read_db()

        # Idempotency: approving the same plan twice returns the stored workflow.
        for wf in db["workflows"]:
            if wf["plan_id"] == plan.plan_id:
                return ApproveResponse(
                    status="already_committed",
                    workflow_id=wf["id"],
                    request_id=wf.get("request_id", ""),
                    committed_at=wf["committed_at"],
                    summary=wf["effects"],
                    executed_steps=[ExecutedStep(**s) for s in wf["executed_steps"]],
                )

        # Validation gate: every referenced lead must exist.
        known = {l["id"] for l in db["leads"]}
        referenced: Set[str] = set()
        if plan.entities.segment:
            referenced.update(plan.entities.segment.lead_ids)
        if plan.entities.billing:
            referenced.update(plan.entities.billing.subscriber_ids)
        unknown = sorted(referenced - known)
        if unknown:
            raise HTTPException(status_code=422, detail=f"Plan references unknown leads: {', '.join(unknown)}")
        if not plan.steps or not any(s.requires_approval for s in plan.steps):
            raise HTTPException(status_code=422, detail="Plan is missing its approval gate step")

        committed = now_utc()
        workflow_id = f"wf-{uuid4().hex[:8]}"
        request_id = f"req-{uuid4().hex[:8]}"

        # Executed steps with sequential timestamps ending at commit time.
        cursor = committed - timedelta(milliseconds=sum(s.duration_ms for s in plan.steps))
        executed: List[ExecutedStep] = []
        for step in plan.steps:
            started = cursor
            cursor = cursor + timedelta(milliseconds=step.duration_ms)
            executed.append(
                ExecutedStep(**step.model_dump(), started_at=iso(started, "milliseconds"), completed_at=iso(cursor, "milliseconds"))
            )

        ent = plan.entities
        effects: Dict[str, Any] = {
            "website_slug": None,
            "leads_segmented": 0,
            "subscribers_added": 0,
            "projected_mrr_added": 0.0,
            "engagement_added": 0,
            "plan_name": None,
            "workflow_id": workflow_id,
        }

        if ent.website:
            slug = unique_slug(db, ent.website.slug)
            db["websites"].append(
                {
                    **ent.website.model_dump(),
                    "id": f"site-{uuid4().hex[:8]}",
                    "slug": slug,
                    "status": "published",
                    "workflow_id": workflow_id,
                    "created_at": iso(committed),
                }
            )
            effects["website_slug"] = slug
            effects["engagement_added"] += 120  # expected launch-day visits

        segment_name = ent.segment.name if ent.segment else None
        tagged_ids: Set[str] = set(ent.segment.lead_ids) if ent.segment else set()
        enrolled_ids: Set[str] = set(ent.billing.subscriber_ids) if ent.billing else set()
        for lead in db["leads"]:
            if lead["id"] in tagged_ids:
                lead["segment"] = segment_name
            if lead["id"] in enrolled_ids:
                lead["status"] = "Offer Sent"
        effects["leads_segmented"] = len(tagged_ids)

        if ent.campaign:
            effects["engagement_added"] += int(round(ent.campaign.audience_size * 0.42 * 10))

        if ent.billing:
            bill = ent.billing
            db["subscription_plans"].append(
                {
                    "id": f"plan-{uuid4().hex[:6]}",
                    "name": bill.plan_name,
                    "price": bill.price,
                    "currency": bill.currency,
                    "interval_days": bill.interval_days,
                    "features": ["Recurring auto-billing", f"Created by AI workflow {workflow_id}"],
                    "subscribers": len(enrolled_ids),
                    "subscriber_ids": sorted(enrolled_ids),
                    "status": "active",
                    "created_at": iso(committed),
                }
            )
            effects["subscribers_added"] = len(enrolled_ids)
            effects["projected_mrr_added"] = bill.projected_mrr
            effects["plan_name"] = bill.plan_name

        # Analytics: append a new live data point derived from the previous one.
        timeline: List[Dict[str, Any]] = db["analytics"]["timeline"]
        last = timeline[-1] if timeline else {"subscriptions": 0, "engagement": 0}
        timeline.append(
            {
                "label": f"W{len(timeline) + 1}",
                "subscriptions": last["subscriptions"] + effects["subscribers_added"],
                "engagement": last["engagement"] + effects["engagement_added"],
            }
        )

        modules = [s.module for s in plan.steps if s.module != "approval"]
        db["ai_requests"].append(
            {
                "id": request_id,
                "prompt": body.prompt,
                "plan_id": plan.plan_id,
                "summary": plan.summary,
                "modules": modules,
                "status": "approved",
                "created_at": iso(committed),
            }
        )
        db["workflows"].append(
            {
                "id": workflow_id,
                "request_id": request_id,
                "plan_id": plan.plan_id,
                "prompt": body.prompt,
                "status": "completed",
                "approved_by": body.approved_by,
                "executed_steps": [s.model_dump() for s in executed],
                "effects": effects,
                "created_at": plan.created_at,
                "committed_at": iso(committed),
            }
        )

        write_db(db)

    return ApproveResponse(
        status="committed",
        workflow_id=workflow_id,
        request_id=request_id,
        committed_at=iso(committed),
        summary=effects,
        executed_steps=executed,
    )
