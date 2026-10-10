"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { KeyboardEvent, ReactNode } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  CircleDashed,
  CreditCard,
  Database,
  DollarSign,
  Globe,
  Loader2,
  Megaphone,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  Terminal,
  TrendingUp,
  Users,
  WifiOff,
  Workflow,
  XCircle,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/* ------------------------------------------------------------------ */
/* API contract (mirrors backend/main.py)                              */
/* ------------------------------------------------------------------ */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ModuleName = "website" | "crm" | "marketing" | "billing" | "approval";

interface PlanStep {
  id: string;
  module: ModuleName;
  title: string;
  detail: string;
  duration_ms: number;
  requires_approval: boolean;
  logs: string[];
  chips: string[];
}

interface WebsiteSpec {
  slug: string;
  title: string;
  headline: string;
  subheadline: string;
  sections: string[];
  theme: string;
}

interface SegmentSpec {
  name: string;
  criteria: string;
  threshold: number;
  lead_ids: string[];
  lead_count: number;
  total_value: number;
}

interface BillingSpec {
  plan_name: string;
  price: number;
  interval_days: number;
  currency: string;
  subscriber_ids: string[];
  projected_mrr: number;
}

interface CampaignSpec {
  name: string;
  channel: string;
  audience_size: number;
  scheduled_for: string;
}

interface Entities {
  topic: string;
  website: WebsiteSpec | null;
  segment: SegmentSpec | null;
  billing: BillingSpec | null;
  campaign: CampaignSpec | null;
}

interface ApprovalSpec {
  title: string;
  message: string;
  sensitive_actions: string[];
  impact: Record<string, number>;
}

interface ExecutionPlan {
  plan_id: string;
  prompt: string;
  summary: string;
  steps: PlanStep[];
  entities: Entities;
  approval: ApprovalSpec;
  created_at: string;
}

interface CommitEffects {
  website_slug: string | null;
  leads_segmented: number;
  subscribers_added: number;
  projected_mrr_added: number;
  engagement_added: number;
  plan_name: string | null;
  workflow_id: string;
}

interface ApproveResponse {
  status: "committed" | "already_committed";
  workflow_id: string;
  request_id: string;
  committed_at: string;
  summary: CommitEffects;
}

interface Lead {
  id: string;
  name: string;
  email: string;
  company: string;
  value: number;
  status: string;
  source: string;
  segment: string | null;
}

interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  interval_days: number;
  subscribers: number;
  status: string;
}

interface TimelinePoint {
  label: string;
  subscriptions: number;
  engagement: number;
}

interface SavedRequest {
  id: string;
  prompt: string;
  plan_id: string;
  summary: string;
  modules: string[];
  status: string;
  created_at: string;
}

interface SavedWebsite {
  id: string;
  slug: string;
  title: string;
  status: string;
}

interface SavedWorkflow {
  id: string;
  status: string;
  committed_at: string;
  effects: CommitEffects;
}

interface Dashboard {
  leads: Lead[];
  subscription_plans: SubscriptionPlan[];
  analytics: { timeline: TimelinePoint[] };
  ai_requests: SavedRequest[];
  websites: SavedWebsite[];
  workflows: SavedWorkflow[];
  kpis: {
    total_leads: number;
    pipeline_value: number;
    active_subscribers: number;
    mrr: number;
    workflows_completed: number;
    websites_live: number;
    segmented_leads: number;
  };
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body: { detail?: unknown } = await res.json();
      if (body.detail !== undefined) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      /* keep default detail */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

/* ------------------------------------------------------------------ */
/* UI helpers                                                          */
/* ------------------------------------------------------------------ */

type Phase =
  | "idle"
  | "planning"
  | "executing"
  | "awaiting_approval"
  | "committing"
  | "complete"
  | "rejected"
  | "error";

type StepStatus = "pending" | "running" | "done" | "waiting" | "rejected";

const EXAMPLE_PROMPTS: string[] = [
  "Create a promo site for our upcoming AI webinar, filter our high-value CRM leads, and generate a 30-day recurring billing plan for them",
  "Launch a landing page for our product launch, segment leads worth over $5k, and email them an announcement",
  "Segment my high-value leads and set up a 14-day billing plan at $199 for them",
];

const GLASS = "rounded-2xl border border-white/10 bg-[#1c1e26]/70 backdrop-blur-xl";

const MODULE_ICON: Record<ModuleName | "commit", LucideIcon> = {
  website: Globe,
  crm: Users,
  marketing: Megaphone,
  billing: CreditCard,
  approval: ShieldAlert,
  commit: Database,
};

const STATUS_STYLE: Record<StepStatus, string> = {
  pending: "border-white/10 bg-[#1c1e26]/40 text-slate-500",
  running:
    "border-[#00f2fe]/60 bg-[#00f2fe]/[0.06] text-slate-100 shadow-[0_0_20px_rgba(0,242,254,0.25)]",
  done: "border-[#22c55e]/40 bg-[#22c55e]/[0.05] text-slate-100",
  waiting: "border-[#f43f5e]/70 bg-[#f43f5e]/[0.08] text-slate-100 shadow-[0_0_25px_rgba(244,63,94,0.4)]",
  rejected: "border-[#f43f5e]/30 bg-[#f43f5e]/[0.04] text-slate-500",
};

const LEAD_STATUS_STYLE: Record<string, string> = {
  Negotiating: "border-[#00f2fe]/30 bg-[#00f2fe]/10 text-[#00f2fe]",
  Qualified: "border-[#22c55e]/30 bg-[#22c55e]/10 text-[#22c55e]",
  "Offer Sent": "border-[#a78bfa]/40 bg-[#a78bfa]/10 text-[#a78bfa]",
  Nurturing: "border-[#fbbf24]/30 bg-[#fbbf24]/10 text-[#fbbf24]",
  New: "border-slate-400/30 bg-slate-400/10 text-slate-300",
  Cold: "border-slate-600/40 bg-slate-600/10 text-slate-500",
};

const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const num = new Intl.NumberFormat("en-US");

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function useCountUp(target: number, duration = 900): number {
  const [value, setValue] = useState<number>(target);
  const from = useRef<number>(target);

  useEffect(() => {
    const start = performance.now();
    const origin = from.current;
    let raf = 0;
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const next = origin + (target - origin) * eased;
      from.current = next;
      setValue(next);
      if (progress < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);

  return value;
}

function Panel({
  title,
  icon: Icon,
  accent = "text-[#00f2fe]",
  right,
  children,
  className = "",
}: {
  title: string;
  icon: LucideIcon;
  accent?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`${GLASS} p-5 ${className}`}>
      <header className="mb-4 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">
          <Icon className={`h-4 w-4 ${accent}`} />
          {title}
        </h2>
        {right}
      </header>
      {children}
    </section>
  );
}

function KpiCard({
  label,
  value,
  format,
  icon: Icon,
  tone,
}: {
  label: string;
  value: number;
  format: (n: number) => string;
  icon: LucideIcon;
  tone: "cyan" | "lime";
}) {
  const animated = useCountUp(value);
  const color = tone === "cyan" ? "text-[#00f2fe]" : "text-[#22c55e]";
  const glow =
    tone === "cyan" ? "shadow-[0_0_18px_rgba(0,242,254,0.12)]" : "shadow-[0_0_18px_rgba(34,197,94,0.12)]";
  return (
    <div className={`${GLASS} ${glow} p-5`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-[0.14em] text-[#64748b]">{label}</span>
        <Icon className={`h-4 w-4 ${color}`} />
      </div>
      <p className={`mt-3 font-mono text-3xl font-bold tabular-nums ${color}`}>{format(animated)}</p>
    </div>
  );
}

function TimelineStep({
  step,
  status,
  isLast,
}: {
  step: { module: ModuleName | "commit"; title: string; detail: string; logs: string[]; chips: string[] };
  status: StepStatus;
  isLast: boolean;
}) {
  const Icon = MODULE_ICON[step.module];
  const stateIcon =
    status === "running" ? (
      <Loader2 className="h-5 w-5 animate-spin text-[#00f2fe]" />
    ) : status === "done" ? (
      <CheckCircle2 className="h-5 w-5 text-[#22c55e]" />
    ) : status === "waiting" ? (
      <AlertTriangle className="h-5 w-5 animate-pulse text-[#f43f5e]" />
    ) : status === "rejected" ? (
      <XCircle className="h-5 w-5 text-[#f43f5e]" />
    ) : (
      <CircleDashed className="h-5 w-5 text-slate-600" />
    );

  return (
    <li className="relative flex gap-4">
      <div className="flex flex-col items-center">
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${STATUS_STYLE[status]}`}
        >
          <Icon className="h-5 w-5" />
        </div>
        {!isLast && (
          <div
            className={`my-1 w-px flex-1 ${status === "done" ? "bg-[#22c55e]/40" : "bg-white/10"}`}
            aria-hidden
          />
        )}
      </div>
      <div className={`mb-4 flex-1 rounded-xl border p-4 transition-all duration-500 ${STATUS_STYLE[status]}`}>
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold tracking-wide">{step.title}</h3>
          {stateIcon}
        </div>
        <p className="mt-1 text-sm text-[#64748b]">{step.detail}</p>
        {status === "done" && step.logs.length > 0 && (
          <pre className="mt-3 overflow-x-auto rounded-lg bg-black/30 p-3 font-mono text-xs leading-relaxed text-[#22c55e]/90">
            {step.logs.join("\n")}
          </pre>
        )}
        {(status === "done" || status === "waiting") && step.chips.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {step.chips.map((chip) => (
              <span
                key={chip}
                className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 font-mono text-[11px] text-slate-300"
              >
                {chip}
              </span>
            ))}
          </div>
        )}
      </div>
    </li>
  );
}

/* ------------------------------------------------------------------ */
/* Page                                                                */
/* ------------------------------------------------------------------ */

export default function Home() {
  const [prompt, setPrompt] = useState<string>("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [plan, setPlan] = useState<ExecutionPlan | null>(null);
  const [statuses, setStatuses] = useState<StepStatus[]>([]);
  const [result, setResult] = useState<ApproveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [offline, setOffline] = useState<boolean>(false);
  const runToken = useRef<number>(0);

  const loadDashboard = useCallback(async () => {
    try {
      const data = await api<Dashboard>("/api/dashboard");
      setDash(data);
      setOffline(false);
    } catch {
      setOffline(true);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
    return () => {
      runToken.current += 1;
    };
  }, [loadDashboard]);

  const setStatus = useCallback((index: number, status: StepStatus) => {
    setStatuses((prev) => prev.map((s, i) => (i === index ? status : s)));
  }, []);

  const runPlan = useCallback(
    async (p: ExecutionPlan, token: number) => {
      setPhase("executing");
      for (let i = 0; i < p.steps.length; i += 1) {
        const step = p.steps[i];
        if (step.requires_approval) {
          setStatus(i, "waiting");
          setPhase("awaiting_approval");
          return;
        }
        setStatus(i, "running");
        await sleep(step.duration_ms);
        if (token !== runToken.current) return;
        setStatus(i, "done");
      }
    },
    [setStatus],
  );

  const submit = useCallback(async () => {
    const text = prompt.trim();
    if (text.length < 3 || phase !== "idle") return;
    runToken.current += 1;
    const token = runToken.current;
    setError(null);
    setResult(null);
    setPlan(null);
    setPhase("planning");
    try {
      const [parsed] = await Promise.all([
        api<ExecutionPlan>("/api/agent/parse", { method: "POST", body: JSON.stringify({ prompt: text }) }),
        sleep(900),
      ]);
      if (token !== runToken.current) return;
      setPlan(parsed);
      setStatuses(new Array<StepStatus>(parsed.steps.length + 1).fill("pending"));
      await runPlan(parsed, token);
    } catch (e) {
      if (token !== runToken.current) return;
      setError(e instanceof Error ? e.message : "Unknown error");
      setPhase("error");
    }
  }, [prompt, phase, runPlan]);

  const approve = useCallback(async () => {
    if (!plan || phase !== "awaiting_approval") return;
    const gateIndex = plan.steps.findIndex((s) => s.requires_approval);
    const commitIndex = plan.steps.length;
    setError(null);
    setPhase("committing");
    setStatus(gateIndex, "done");
    setStatus(commitIndex, "running");
    try {
      const [res] = await Promise.all([
        api<ApproveResponse>("/api/agent/approve", {
          method: "POST",
          body: JSON.stringify({ prompt: plan.prompt, plan, approved_by: "operator" }),
        }),
        sleep(1200),
      ]);
      setResult(res);
      setStatus(commitIndex, "done");
      await loadDashboard();
      setPhase("complete");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Commit failed");
      setStatus(gateIndex, "waiting");
      setStatus(commitIndex, "pending");
      setPhase("awaiting_approval");
    }
  }, [plan, phase, setStatus, loadDashboard]);

  const reject = useCallback(() => {
    if (!plan || phase !== "awaiting_approval") return;
    const gateIndex = plan.steps.findIndex((s) => s.requires_approval);
    setStatus(gateIndex, "rejected");
    setStatus(plan.steps.length, "rejected");
    setPhase("rejected");
  }, [plan, phase, setStatus]);

  const reset = useCallback(() => {
    runToken.current += 1;
    setPhase("idle");
    setPlan(null);
    setStatuses([]);
    setResult(null);
    setError(null);
    setPrompt("");
  }, []);

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submit();
    }
  };

  const timelineSteps = plan
    ? [
        ...plan.steps,
        {
          id: "commit",
          module: "commit" as const,
          title: "Commit & Persist",
          detail: "Writing workflow, website, billing plan and analytics to nexus_db.json.",
          duration_ms: 0,
          requires_approval: false,
          logs: ["> state saved to backend/nexus_db.json"],
          chips: ["persisted"],
        },
      ]
    : [];

  const busy = phase !== "idle";
  const latest = dash && dash.ai_requests.length > 0 ? dash.ai_requests[dash.ai_requests.length - 1] : null;
  const latestWorkflow = dash && dash.workflows.length > 0 ? dash.workflows[dash.workflows.length - 1] : null;
  const sortedLeads = dash ? [...dash.leads].sort((a, b) => b.value - a.value) : [];

  return (
    <main className="mx-auto min-h-screen w-full max-w-7xl px-4 pb-20 pt-6 sm:px-6">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#00f2fe]/40 bg-[#00f2fe]/10 shadow-[0_0_20px_rgba(0,242,254,0.35)]">
            <Zap className="h-5 w-5 text-[#00f2fe]" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-[0.28em] text-slate-100">BLACKOUT</h1>
            <p className="text-xs text-[#64748b]">AI business operating system</p>
          </div>
        </div>
        <div
          className={`flex items-center gap-2 rounded-full border px-3 py-1.5 font-mono text-xs ${
            offline
              ? "border-[#f43f5e]/40 bg-[#f43f5e]/10 text-[#f43f5e]"
              : "border-[#22c55e]/30 bg-[#22c55e]/10 text-[#22c55e]"
          }`}
        >
          {offline ? <WifiOff className="h-3.5 w-3.5" /> : <span className="h-2 w-2 animate-pulse rounded-full bg-[#22c55e]" />}
          {offline ? "backend offline" : "agent online"}
        </div>
      </header>

      {offline && (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#f43f5e]/40 bg-[#f43f5e]/10 p-4 text-sm text-[#fecdd3]">
          <span>
            Cannot reach the API at <code className="font-mono">{API_URL}</code>. Start it with{" "}
            <code className="font-mono">uvicorn main:app --reload --port 8000</code> inside <code className="font-mono">backend/</code>.
          </span>
          <button
            onClick={() => void loadDashboard()}
            className="rounded-lg border border-[#f43f5e]/60 px-3 py-1.5 font-medium text-[#f43f5e] transition hover:bg-[#f43f5e]/10"
          >
            Retry
          </button>
        </div>
      )}

      {/* Command bar */}
      <section className="mb-8">
        <div className="neon-border rounded-2xl bg-gradient-to-r from-[#00f2fe] via-[#818cf8] to-[#f43f5e] p-[1.5px] shadow-[0_0_40px_rgba(0,242,254,0.25)]">
          <div className="rounded-2xl bg-[#0d0f15]/95 p-5">
            <div className="mb-3 flex items-center justify-between">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#00f2fe]">
                <Sparkles className="h-4 w-4" />
                AI Business Agent
              </span>
              <span className="hidden font-mono text-[11px] text-[#64748b] sm:block">
                natural language in, multi-step workflow out
              </span>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={onKeyDown}
                disabled={busy}
                rows={3}
                placeholder="Tell the agent what to do, e.g. “Create a promo site for our upcoming AI webinar, filter our high-value CRM leads, and generate a 30-day recurring billing plan for them”"
                className="min-h-[88px] flex-1 resize-none rounded-xl border border-white/10 bg-black/30 p-4 font-mono text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-[#00f2fe]/60 focus:shadow-[0_0_20px_rgba(0,242,254,0.2)] disabled:opacity-60"
              />
              {phase === "complete" || phase === "rejected" || phase === "error" ? (
                <button
                  onClick={reset}
                  className="flex h-12 items-center justify-center gap-2 rounded-xl border border-[#00f2fe]/50 px-6 text-sm font-semibold text-[#00f2fe] transition hover:bg-[#00f2fe]/10 hover:shadow-[0_0_20px_rgba(0,242,254,0.3)]"
                >
                  <RotateCcw className="h-4 w-4" />
                  New command
                </button>
              ) : (
                <button
                  onClick={() => void submit()}
                  disabled={busy || prompt.trim().length < 3}
                  className="flex h-12 items-center justify-center gap-2 rounded-xl bg-[#00f2fe] px-6 text-sm font-bold text-[#06141a] shadow-[0_0_25px_rgba(0,242,254,0.5)] transition hover:shadow-[0_0_40px_rgba(0,242,254,0.8)] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
                >
                  {phase === "planning" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
                  {phase === "planning" ? "Planning" : "Execute"}
                </button>
              )}
            </div>
            {phase === "idle" && (
              <div className="mt-4 flex flex-wrap gap-2">
                {EXAMPLE_PROMPTS.map((example) => (
                  <button
                    key={example}
                    onClick={() => setPrompt(example)}
                    className="max-w-full truncate rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-left text-xs text-slate-400 transition hover:border-[#00f2fe]/40 hover:text-[#00f2fe]"
                    title={example}
                  >
                    {example.length > 74 ? `${example.slice(0, 74)}…` : example}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Execution screen */}
      {phase !== "idle" && (
        <section className="animate-rise mb-8 grid gap-6 lg:grid-cols-5">
          <div className={`${GLASS} p-6 lg:col-span-3`}>
            <div className="mb-5 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">
                <Terminal className="h-4 w-4 text-[#00f2fe]" />
                Live Execution
              </h2>
              <span className="font-mono text-[11px] text-[#64748b]">{plan ? plan.plan_id : "..."}</span>
            </div>

            {phase === "planning" && (
              <div className="flex items-center gap-3 rounded-xl border border-[#00f2fe]/30 bg-[#00f2fe]/[0.05] p-4 font-mono text-sm text-[#00f2fe] shadow-[0_0_20px_rgba(0,242,254,0.2)]">
                <Loader2 className="h-4 w-4 animate-spin" />
                parsing instruction and building execution plan…
              </div>
            )}

            {plan && (
              <>
                <p className="mb-5 rounded-lg border border-white/10 bg-black/20 p-3 font-mono text-xs text-slate-400">
                  <span className="text-[#00f2fe]">❯</span> {plan.prompt}
                  <br />
                  <span className="text-[#64748b]">{plan.summary}</span>
                </p>
                <ol>
                  {timelineSteps.map((step, i) => (
                    <TimelineStep
                      key={step.id}
                      step={step}
                      status={statuses[i] ?? "pending"}
                      isLast={i === timelineSteps.length - 1}
                    />
                  ))}
                </ol>
              </>
            )}

            {phase === "error" && error && (
              <div className="rounded-xl border border-[#f43f5e]/40 bg-[#f43f5e]/10 p-4 text-sm text-[#fecdd3]">
                <p className="font-semibold text-[#f43f5e]">Agent error</p>
                <p className="mt-1 font-mono text-xs">{error}</p>
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            {(phase === "awaiting_approval" || phase === "committing") && plan && (
              <div className="animate-alarm animate-rise rounded-2xl border border-[#f43f5e]/70 bg-[#f43f5e]/[0.07] p-6 backdrop-blur-xl">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-[#f43f5e]/60 bg-[#f43f5e]/15 shadow-[0_0_20px_rgba(244,63,94,0.5)]">
                    <ShieldAlert className="h-6 w-6 text-[#f43f5e]" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#f43f5e]">Approval Gate</p>
                    <h3 className="text-lg font-bold text-slate-100">{plan.approval.title}</h3>
                  </div>
                </div>
                <p className="mt-4 text-sm text-slate-300">{plan.approval.message}</p>
                <ul className="mt-4 space-y-2">
                  {plan.approval.sensitive_actions.map((action) => (
                    <li key={action} className="flex gap-2 text-sm text-slate-200">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#f43f5e]" />
                      {action}
                    </li>
                  ))}
                </ul>
                <dl className="mt-5 grid grid-cols-3 gap-3 text-center">
                  <div className="rounded-lg border border-white/10 bg-black/25 p-3">
                    <dt className="text-[10px] uppercase tracking-wider text-[#64748b]">Leads</dt>
                    <dd className="font-mono text-lg font-bold text-slate-100">
                      {num.format(plan.approval.impact.leads_affected ?? 0)}
                    </dd>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-black/25 p-3">
                    <dt className="text-[10px] uppercase tracking-wider text-[#64748b]">Pipeline</dt>
                    <dd className="font-mono text-lg font-bold text-slate-100">
                      {usd.format(plan.approval.impact.pipeline_value ?? 0)}
                    </dd>
                  </div>
                  <div className="rounded-lg border border-white/10 bg-black/25 p-3">
                    <dt className="text-[10px] uppercase tracking-wider text-[#64748b]">+MRR</dt>
                    <dd className="font-mono text-lg font-bold text-[#22c55e]">
                      {usd.format(plan.approval.impact.projected_mrr ?? 0)}
                    </dd>
                  </div>
                </dl>
                {error && (
                  <p className="mt-4 rounded-lg border border-[#f43f5e]/40 bg-black/30 p-3 font-mono text-xs text-[#fecdd3]">
                    {error}
                  </p>
                )}
                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => void approve()}
                    disabled={phase === "committing"}
                    className="flex h-12 flex-1 items-center justify-center gap-2 rounded-xl bg-[#f43f5e] text-sm font-bold text-white shadow-[0_0_25px_rgba(244,63,94,0.6)] transition hover:shadow-[0_0_40px_rgba(244,63,94,0.9)] disabled:cursor-wait disabled:opacity-60"
                  >
                    {phase === "committing" ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4" />
                    )}
                    {phase === "committing" ? "Committing…" : "Approve"}
                  </button>
                  <button
                    onClick={reject}
                    disabled={phase === "committing"}
                    className="h-12 rounded-xl border border-white/15 px-5 text-sm font-semibold text-slate-300 transition hover:border-[#f43f5e]/50 hover:text-[#f43f5e] disabled:opacity-40"
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}

            {phase === "complete" && result && (
              <div className="animate-rise rounded-2xl border border-[#22c55e]/50 bg-[#22c55e]/[0.06] p-6 shadow-[0_0_35px_rgba(34,197,94,0.25)] backdrop-blur-xl">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-8 w-8 text-[#22c55e]" />
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#22c55e]">
                      {result.status === "already_committed" ? "Already committed" : "Workflow committed"}
                    </p>
                    <h3 className="text-lg font-bold text-slate-100">Saved to nexus_db.json</h3>
                  </div>
                </div>
                <dl className="mt-5 space-y-2 font-mono text-sm">
                  {result.summary.website_slug && (
                    <div className="flex justify-between gap-4">
                      <dt className="text-[#64748b]">Website</dt>
                      <dd className="text-slate-100">/{result.summary.website_slug}</dd>
                    </div>
                  )}
                  <div className="flex justify-between gap-4">
                    <dt className="text-[#64748b]">Leads segmented</dt>
                    <dd className="text-slate-100">{result.summary.leads_segmented}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-[#64748b]">Subscribers added</dt>
                    <dd className="text-[#22c55e]">+{result.summary.subscribers_added}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-[#64748b]">MRR added</dt>
                    <dd className="text-[#22c55e]">+{usd.format(result.summary.projected_mrr_added)}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-[#64748b]">Engagement</dt>
                    <dd className="text-[#00f2fe]">+{num.format(result.summary.engagement_added)}</dd>
                  </div>
                  <div className="flex justify-between gap-4 border-t border-white/10 pt-2">
                    <dt className="text-[#64748b]">Workflow</dt>
                    <dd className="text-slate-100">{result.workflow_id}</dd>
                  </div>
                </dl>
                <a
                  href="#dashboard"
                  className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#00f2fe] hover:underline"
                >
                  See live analytics <ArrowRight className="h-4 w-4" />
                </a>
              </div>
            )}

            {phase === "rejected" && (
              <div className="animate-rise rounded-2xl border border-white/10 bg-[#1c1e26]/70 p-6 backdrop-blur-xl">
                <XCircle className="h-8 w-8 text-[#f43f5e]" />
                <h3 className="mt-3 text-lg font-bold text-slate-100">Execution halted</h3>
                <p className="mt-2 text-sm text-slate-400">
                  Authorization was denied at the Approval Gate. Nothing was written to nexus_db.json.
                </p>
              </div>
            )}

            {(phase === "planning" || phase === "executing") && (
              <div className={`${GLASS} p-6`}>
                <p className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.14em] text-[#00f2fe]">
                  <Workflow className="h-4 w-4" /> Agent working
                </p>
                <p className="mt-3 text-sm text-[#64748b]">
                  Coordinating modules against a shared data layer. The agent will pause before any sensitive operation
                  and wait for your authorization.
                </p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Dashboard */}
      <div id="dashboard" className="scroll-mt-6">
        {!dash && !offline && (
          <div className="flex items-center gap-3 font-mono text-sm text-[#64748b]">
            <Loader2 className="h-4 w-4 animate-spin" /> loading dashboard…
          </div>
        )}

        {dash && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <KpiCard label="Pipeline value" value={dash.kpis.pipeline_value} format={(n) => usd.format(n)} icon={TrendingUp} tone="cyan" />
              <KpiCard label="Active subscribers" value={dash.kpis.active_subscribers} format={(n) => num.format(Math.round(n))} icon={Users} tone="lime" />
              <KpiCard label="Monthly recurring revenue" value={dash.kpis.mrr} format={(n) => usd.format(n)} icon={DollarSign} tone="lime" />
              <KpiCard label="Workflows committed" value={dash.kpis.workflows_completed} format={(n) => num.format(Math.round(n))} icon={Workflow} tone="cyan" />
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              <Panel
                title="Subscriptions & Marketing"
                icon={TrendingUp}
                accent="text-[#22c55e]"
                className="lg:col-span-2"
                right={<span className="font-mono text-[11px] text-[#64748b]">weekly, live from backend</span>}
              >
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={dash.analytics.timeline} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                      <defs>
                        <linearGradient id="gradSubs" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#22c55e" stopOpacity={0.45} />
                          <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradEng" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#00f2fe" stopOpacity={0.35} />
                          <stop offset="100%" stopColor="#00f2fe" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 6" vertical={false} />
                      <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} fontSize={12} />
                      <YAxis yAxisId="left" stroke="#22c55e" tickLine={false} axisLine={false} fontSize={12} domain={["dataMin - 10", "auto"]} />
                      <YAxis yAxisId="right" orientation="right" stroke="#00f2fe" tickLine={false} axisLine={false} fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          background: "rgba(13,15,21,0.95)",
                          border: "1px solid rgba(255,255,255,0.12)",
                          borderRadius: 12,
                          color: "#e2e8f0",
                          fontSize: 12,
                        }}
                        labelStyle={{ color: "#64748b" }}
                      />
                      <Legend wrapperStyle={{ fontSize: 12, color: "#64748b" }} />
                      <Area
                        yAxisId="left"
                        type="monotone"
                        dataKey="subscriptions"
                        name="Active subscriptions"
                        stroke="#22c55e"
                        strokeWidth={2.5}
                        fill="url(#gradSubs)"
                        style={{ filter: "drop-shadow(0 0 6px rgba(34,197,94,0.7))" }}
                        animationDuration={1200}
                      />
                      <Area
                        yAxisId="right"
                        type="monotone"
                        dataKey="engagement"
                        name="Campaign engagement"
                        stroke="#00f2fe"
                        strokeWidth={2.5}
                        fill="url(#gradEng)"
                        style={{ filter: "drop-shadow(0 0 6px rgba(0,242,254,0.7))" }}
                        animationDuration={1200}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </Panel>

              <Panel title="Latest AI Request" icon={Sparkles} accent="text-[#00f2fe]">
                {latest ? (
                  <div className="space-y-4">
                    <p className="rounded-lg border border-white/10 bg-black/25 p-3 font-mono text-xs leading-relaxed text-slate-300">
                      <span className="text-[#00f2fe]">❯</span> {latest.prompt}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {latest.modules.map((m, i) => (
                        <span
                          key={`${m}-${i}`}
                          className="rounded-md border border-[#00f2fe]/30 bg-[#00f2fe]/10 px-2 py-0.5 font-mono text-[11px] uppercase text-[#00f2fe]"
                        >
                          {m}
                        </span>
                      ))}
                    </div>
                    <dl className="space-y-2 text-sm">
                      <div className="flex justify-between gap-4">
                        <dt className="text-[#64748b]">Status</dt>
                        <dd className="flex items-center gap-1.5 font-semibold text-[#22c55e]">
                          <CheckCircle2 className="h-4 w-4" /> {latest.status}
                        </dd>
                      </div>
                      <div className="flex justify-between gap-4">
                        <dt className="text-[#64748b]">Committed</dt>
                        <dd className="font-mono text-slate-200">{formatTime(latest.created_at)}</dd>
                      </div>
                      {latestWorkflow && (
                        <>
                          <div className="flex justify-between gap-4">
                            <dt className="text-[#64748b]">Workflow</dt>
                            <dd className="font-mono text-slate-200">{latestWorkflow.id}</dd>
                          </div>
                          <div className="flex justify-between gap-4">
                            <dt className="text-[#64748b]">MRR added</dt>
                            <dd className="font-mono text-[#22c55e]">
                              +{usd.format(latestWorkflow.effects.projected_mrr_added)}
                            </dd>
                          </div>
                        </>
                      )}
                    </dl>
                  </div>
                ) : (
                  <div className="flex h-full min-h-[200px] flex-col items-center justify-center text-center">
                    <Database className="h-8 w-8 text-slate-600" />
                    <p className="mt-3 text-sm text-slate-400">No committed requests yet.</p>
                    <p className="mt-1 text-xs text-[#64748b]">
                      Run a command above and approve it. It will be saved to nexus_db.json and appear here.
                    </p>
                  </div>
                )}
              </Panel>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              <Panel
                title="Intelligent CRM"
                icon={Users}
                className="lg:col-span-2"
                right={<span className="font-mono text-[11px] text-[#64748b]">{dash.leads.length} leads</span>}
              >
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-left text-sm">
                    <thead>
                      <tr className="border-b border-white/10 text-[11px] uppercase tracking-wider text-[#64748b]">
                        <th className="pb-3 font-medium">Lead</th>
                        <th className="pb-3 font-medium">Email</th>
                        <th className="pb-3 text-right font-medium">Value</th>
                        <th className="pb-3 pl-4 font-medium">Status</th>
                        <th className="pb-3 font-medium">Segment</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedLeads.map((lead) => (
                        <tr
                          key={lead.id}
                          className={`border-b border-white/5 transition hover:bg-white/[0.03] ${
                            lead.segment ? "bg-[#00f2fe]/[0.04]" : ""
                          }`}
                        >
                          <td className="py-3">
                            <p className="font-medium text-slate-100">{lead.name}</p>
                            <p className="text-xs text-[#64748b]">{lead.company}</p>
                          </td>
                          <td className="py-3 font-mono text-xs text-slate-400">{lead.email}</td>
                          <td className="py-3 text-right font-mono font-semibold text-[#22c55e]">
                            {usd.format(lead.value)}
                          </td>
                          <td className="py-3 pl-4">
                            <span
                              className={`rounded-md border px-2 py-0.5 text-xs font-medium ${
                                LEAD_STATUS_STYLE[lead.status] ?? LEAD_STATUS_STYLE.New
                              }`}
                            >
                              {lead.status}
                            </span>
                          </td>
                          <td className="py-3 text-xs text-[#00f2fe]">{lead.segment ?? <span className="text-slate-600">-</span>}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>

              <div className="space-y-6">
                <Panel title="Subscription Plans" icon={CreditCard} accent="text-[#22c55e]">
                  <ul className="space-y-3">
                    {dash.subscription_plans.map((p) => (
                      <li
                        key={p.id}
                        className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/20 p-3"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-100">{p.name}</p>
                          <p className="font-mono text-xs text-[#64748b]">
                            {usd.format(p.price)} / {p.interval_days}d
                          </p>
                        </div>
                        <span className="font-mono text-sm font-bold text-[#22c55e]">{num.format(p.subscribers)} subs</span>
                      </li>
                    ))}
                  </ul>
                </Panel>

                <Panel title="Generated Websites" icon={Globe}>
                  {dash.websites.length === 0 ? (
                    <p className="text-sm text-[#64748b]">No sites published yet.</p>
                  ) : (
                    <ul className="space-y-3">
                      {dash.websites.map((w) => (
                        <li
                          key={w.id}
                          className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/20 p-3"
                        >
                          <span className="truncate font-mono text-sm text-slate-200">/{w.slug}</span>
                          <span className="rounded-md border border-[#22c55e]/30 bg-[#22c55e]/10 px-2 py-0.5 text-xs text-[#22c55e]">
                            {w.status}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Panel>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
