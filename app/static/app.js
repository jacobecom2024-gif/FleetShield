const $ = (selector) => document.querySelector(selector);

const ui = {
  runDemo: $("#run-demo"),
  reset: $("#reset"),
  fault: $("#fault"),
  runVulnerable: $("#run-vulnerable"),
  discover: $("#discover"),
  activate: $("#activate"),
  replay: $("#replay"),
  ledger: $("#ledger"),
  trace: $("#trace"),
  policies: $("#policies"),
  effectCount: $("#effect-count"),
  verdict: $("#verdict"),
  traceCount: $("#trace-count"),
  proofScore: $("#proof-score"),
  proofCopy: $("#proof-copy"),
  meter: $("#meter-fill"),
  runtimeVerdict: $("#runtime-verdict"),
  runtimeExecution: $("#runtime-execution"),
  runtimeModel: $("#runtime-model"),
  runtimeCompute: $("#runtime-compute"),
  runtimeState: $("#runtime-state"),
  runtimePubsub: $("#runtime-pubsub"),
};

let stage = 0;
let activePolicyId = null;

async function request(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.error || "Request failed");
  return data;
}

async function refreshEvidence() {
  const response = await fetch("/api/evidence", { cache: "no-store" });
  const evidence = await response.json();
  const runtime = evidence.runtime;
  const proof = evidence.qualifying_evidence;
  ui.runtimeExecution.textContent = runtime.contract_miner;
  ui.runtimeModel.textContent = runtime.model;
  ui.runtimeCompute.textContent = runtime.cloud_run
    ? `Cloud Run · ${runtime.cloud_run_revision}`
    : "local";
  ui.runtimeState.textContent = runtime.state_backend;
  ui.runtimePubsub.textContent = proof.pubsub_events_observed ? "observed" : "not observed";
  const cloudProof = proof.google_adk_executed && proof.cloud_run_active;
  ui.runtimeVerdict.textContent = cloudProof
    ? "Cloud + ADK + Gemini execution verified"
    : "Reproducible local proof — cloud claims disabled";
  ui.runtimeVerdict.className = cloudProof ? "verified" : "local-proof";
}

function setStage(next, copy) {
  stage = next;
  ui.proofScore.innerHTML = `${stage}<span>/4</span>`;
  ui.meter.style.width = `${stage * 25}%`;
  ui.proofCopy.textContent = copy;
  ui.discover.disabled = stage < 1;
  ui.activate.disabled = stage < 2;
  ui.replay.disabled = stage < 3;
}

function renderResult(result) {
  ui.effectCount.textContent = result.actual_effects;
  ui.verdict.textContent = result.safe ? "SAFE" : "VIOLATED";
  ui.verdict.className = `verdict ${result.safe ? "safe" : "danger"}`;
  ui.ledger.innerHTML = result.ledger.length
    ? result.ledger.map((entry, index) => `
      <div class="ledger-entry ${index > 0 ? "duplicate" : ""}">
        <small>${index > 0 ? "DUPLICATE EFFECT" : "COMMITTED EFFECT"}</small>
        <b>${entry.currency} ${entry.amount.toFixed(2)}</b>
        <small>${entry.subject_id}<br>${entry.action_id.slice(0, 13)}…</small>
      </div>`).join("")
    : '<div class="empty">No side effect was committed.</div>';

  ui.traceCount.textContent = `${result.trace.length} events`;
  ui.trace.innerHTML = result.trace.map((event) => `
    <li class="${event.status}">
      <span class="seq">${String(event.sequence).padStart(2, "0")}</span>
      <span class="message">${escapeHtml(event.message)}</span>
      <span class="time">${new Date(event.occurred_at).toLocaleTimeString([], {hour12:false})}</span>
    </li>`).join("");
}

function renderPolicies(policies) {
  ui.policies.innerHTML = policies.map((policy) => `
    <div class="policy-card">
      <header>
        <h3>${escapeHtml(policy.name)}</h3>
        <span class="policy-state ${policy.state}">${policy.state}</span>
      </header>
      <div class="expression">${escapeHtml(policy.expression)}</div>
      <small>scope: ${policy.scope.join(", ")}</small>
    </div>`).join("");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[char]);
}

async function resetAll() {
  await request("/api/reset", { keep_policies: false });
  activePolicyId = null;
  ui.ledger.innerHTML = '<div class="empty">The sandbox ledger is empty.</div>';
  ui.trace.innerHTML = '<li class="trace-empty">Run an experiment to generate evidence.</li>';
  ui.policies.innerHTML = '<div class="empty">No invariant has been discovered.</div>';
  ui.effectCount.textContent = "0";
  ui.traceCount.textContent = "0 events";
  ui.verdict.textContent = "READY";
  ui.verdict.className = "verdict neutral";
  setStage(0, "Ready to inject a controlled failure.");
}

async function runVulnerable() {
  await request("/api/reset", { keep_policies: false });
  const result = await request("/api/run", { fault: ui.fault.value });
  renderResult(result);
  if (result.safe) {
    setStage(1, "The fault was tolerated; choose a side-effect-after-commit fault to expose duplication.");
  } else {
    setStage(1, "Counterexample captured: the operational invariant failed.");
  }
}

async function discover() {
  const data = await request("/api/discover");
  activePolicyId = data.policies.find((policy) => policy.invariant_type === "exactly_once")?.policy_id;
  renderPolicies(data.policies);
  await refreshEvidence();
  setStage(2, "Three candidate controls compiled in shadow mode.");
}

async function activate() {
  await request("/api/activate", { policy_id: activePolicyId, approved_by: "hackathon-demo-reviewer" });
  const state = await fetch("/api/state").then((response) => response.json());
  renderPolicies(state.policies);
  setStage(3, "Exactly-once control approved and propagated to the community-relief fleet.");
}

async function replay() {
  await request("/api/reset", { keep_policies: true });
  const result = await request("/api/run", { fault: ui.fault.value });
  renderResult(result);
  setStage(4, result.safe
    ? "Proof complete: exact replay produced one effect and blocked the duplicate."
    : "Replay still violates the invariant; the control is not accepted.");
}

async function fullDemo() {
  ui.runDemo.disabled = true;
  try {
    await resetAll();
    await runVulnerable();
    await new Promise((resolve) => setTimeout(resolve, 650));
    await discover();
    await new Promise((resolve) => setTimeout(resolve, 650));
    await activate();
    await new Promise((resolve) => setTimeout(resolve, 650));
    await replay();
  } catch (error) {
    ui.proofCopy.textContent = error.message;
  } finally {
    ui.runDemo.disabled = false;
  }
}

ui.reset.addEventListener("click", () => resetAll().catch(console.error));
ui.runVulnerable.addEventListener("click", () => runVulnerable().catch((error) => ui.proofCopy.textContent = error.message));
ui.discover.addEventListener("click", () => discover().catch((error) => ui.proofCopy.textContent = error.message));
ui.activate.addEventListener("click", () => activate().catch((error) => ui.proofCopy.textContent = error.message));
ui.replay.addEventListener("click", () => replay().catch((error) => ui.proofCopy.textContent = error.message));
ui.runDemo.addEventListener("click", fullDemo);
refreshEvidence().catch(() => {
  ui.runtimeVerdict.textContent = "Runtime evidence unavailable";
});
