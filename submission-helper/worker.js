"use strict";

const REPOSITORY = "https://github.com/atharvatripathi2026/gtgoats_mech_royale";
const QUEUE_URL = "https://raw.githubusercontent.com/atharvatripathi2026/gtgoats_mech_royale/practice-queue/queue.json";
const TRACK = "https://www.joinbuilders.org/buildathon/tracks/builders";
const CUTOFF = Date.parse("2026-11-22T16:00:00Z");
const HOUR = 60 * 60 * 1000;
const GAP = 15 * 60 * 1000 + 1000;
const LEASE_MS = 60 * 1000;
const STATE_KEY = "practiceSubmissionState";
const ALARM = "practice-wake";
const ORIGINAL = [
  "4cb4a9ea753e8df3744a9ba8d44053068e64e535",
  "9e59bbfd46f562dbb88d0a4377dc333ce2f8c273",
  "ce73f3e213a1c7bcc1fb65a90b4edf6e76133c13",
  "03a8f93fb36afa5db4a08f211d1d1aa6dcbcae8e"
];
const INITIAL_ANCHORS = [
  {receipt: "BB-073A1E2D", commit: ORIGINAL[0]}, {receipt: "BB-C6067CA3", commit: ORIGINAL[1]}
];
const INITIAL_SCORES = [3.60, 3.23, 3.65, 3.71];
const SHA = /^[0-9a-f]{40}$/i;
const PROGRESS = new Map([["Queued", 0], ["Scoring", 1], ["Scoring problem", 2],
  ["Rejected", 2], ["Scored", 3], ["Scored under a previous version", 4]]);

// All read/modify/write operations share one sequence, including alarm and restart handling.
// Durable reservations precede replies. A lost dispatch reply can never authorize a second click.
let tail = Promise.resolve();
function serialized(operation) {
  const result = tail.then(operation);
  tail = result.catch(() => {});
  return result;
}

async function loadState() {
  const saved = (await chrome.storage.local.get(STATE_KEY))[STATE_KEY];
  if (saved !== undefined) {
    if (!saved || saved.version !== 1 || !Array.isArray(saved.attempts) ||
        !Array.isArray(saved.tabs) || !Array.isArray(saved.seen)) {
      throw new Error("Stored practice history could not be read.");
    }
    return saved;
  }
  return {version: 1, enabled: false, startedAt: null, lease: null, attempts: [], tabs: [], seen: [], manual: [], results: []};
}

function save(state) {
  return chrome.storage.local.set({[STATE_KEY]: state});
}

function allowedSender(sender) {
  if (sender?.id !== chrome.runtime.id || sender.frameId !== 0 ||
      !Number.isInteger(sender.tab?.id) || sender.tab.id < 0) return false;
  try {
    const url = new URL(sender.url);
    return url.origin + url.pathname.replace(/\/$/, "") === TRACK;
  } catch {
    return false;
  }
}

let cachedQueue = null;
let cachedAt = 0;
async function candidates(refresh = false) {
  const now = Date.now();
  if (!refresh && cachedQueue && now - cachedAt < 45_000) return cachedQueue;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 7000);
  try {
    const response = await fetch(QUEUE_URL, {method: "GET", credentials: "omit", redirect: "error",
      referrerPolicy: "no-referrer", cache: "no-store", signal: controller.signal});
    if (!response.ok) throw new Error("The public candidate queue is unavailable.");
    const queue = await response.json();
    if (!queue || queue.version !== 1 || queue.repository !== REPOSITORY ||
        !Array.isArray(queue.candidates) || queue.candidates.length > 256 ||
        !queue.candidates.every(c => c && typeof c.commit === "string" && SHA.test(c.commit) &&
          (c.parents === undefined || Array.isArray(c.parents) && c.parents.length <= 32 &&
            c.parents.every(p => typeof p === "string" && SHA.test(p))))) {
      throw new Error("The public candidate queue did not validate.");
    }
    const unique = new Map();
    for (const entry of queue.candidates) {
      const commit = entry.commit.toLowerCase();
      if (!unique.has(commit)) unique.set(commit, {commit, parents: (entry.parents || []).map(p => p.toLowerCase())});
    }
    cachedQueue = [...unique.values()];
    cachedAt = now;
    return cachedQueue;
  } finally {
    clearTimeout(timer);
  }
}

function validView(view) {
  return view && view.historyReady === true && typeof view.queued === "boolean" &&
    (view.remaining === null || Number.isInteger(view.remaining) && view.remaining >= 0 && view.remaining <= 4) &&
    (view.retryAt == null || Number.isFinite(view.retryAt)) &&
    Array.isArray(view.commits) && view.commits.length <= 512 &&
    view.commits.every(c => typeof c === "string" && /^[0-9a-f]{7,40}$/i.test(c));
}

function matches(commit, prefix) {
  return commit.startsWith(prefix.toLowerCase());
}

function historyIncludes(view, commit) {
  return view.commits.some(prefix => matches(commit, prefix));
}

function sameTeam(state, view) {
  if (view.identityVerified !== true || view.team !== "GT Goats" ||
      !Array.isArray(view.receipts) || view.receipts.length > 512) return false;
  return anchors(state).some(a => view.receipts.some(row => row && row.receipt === a.receipt &&
    typeof row.commit === "string" && /^[0-9a-f]{7,40}$/i.test(row.commit) && matches(a.commit, row.commit)));
}

function anchors(state) {
  const proofs = new Map(INITIAL_ANCHORS.map(a => [a.receipt, a]));
  const trusted = new Set([...ORIGINAL, ...state.attempts.map(a => a.commit)]);
  for (const {receipt, commit} of state.results || []) {
    if (trusted.has(commit)) proofs.set(receipt, {receipt, commit});
  }
  return [...proofs.values()];
}

function unresolved(attempt) {
  return attempt.status === "dispatched" || attempt.status === "uncertain";
}

function reconcile(state, view, now) {
  // Track visible history locally so a temporarily paginated or abbreviated
  // list cannot turn an already-seen entry into an eligible candidate.
  const prefixes = view.commits.map(c => c.toLowerCase());
  const ours = [...ORIGINAL, ...state.attempts.map(a => a.commit)];
  state.manual = (state.manual || []).filter(m => m.at > now - HOUR);
  if (state.seen.length) {
    for (const prefix of prefixes) {
      const familiar = state.seen.some(old => old.startsWith(prefix) || prefix.startsWith(old));
      if (!familiar && !ours.some(commit => matches(commit, prefix))) {
        state.manual.push({prefix, at: now});
      }
    }
  }
  state.seen = [...new Set([...state.seen, ...prefixes])].slice(-1024);
  const known = [...new Set([...ours, ...(state.knownQueue || [])])];
  state.results ??= [];
  for (const row of view.receipts) {
    if (!row || !PROGRESS.has(row.status) || typeof row.receipt !== "string" || !/^BB-[A-Z0-9]{4,32}$/.test(row.receipt) ||
        typeof row.commit !== "string" || !/^[0-9a-f]{7,40}$/i.test(row.commit)) continue;
    const possibilities = known.filter(c => matches(c, row.commit));
    if (possibilities.length !== 1) continue;
    const commit = possibilities[0];
    if (!prefixes.some(prefix => matches(commit, prefix))) continue;
    if (INITIAL_ANCHORS.some(a => a.receipt === row.receipt && a.commit !== commit)) continue;
    let stored = state.results.find(r => r.receipt === row.receipt);
    if (stored && (stored.commit !== commit || PROGRESS.get(stored.status) > PROGRESS.get(row.status))) continue;
    if (!stored) {
      stored = {commit, receipt: row.receipt, score: null, message: null, firstSeenAt: now};
      state.results.push(stored);
    }
    stored.status = row.status;
    stored.lastSeenAt = now;
    if (Number.isFinite(row.score)) stored.score = row.score;
    if (typeof row.message === "string" && row.message.trim()) stored.message = row.message.slice(0, 4096);
  }
  for (const attempt of state.attempts) {
    if (attempt.status === "confirmed") continue;
    const found = prefixes.some(prefix => matches(attempt.commit, prefix) &&
      known.filter(c => matches(c, prefix)).length === 1);
    if (found) {
      attempt.status = "confirmed";
      attempt.confirmedAt = now;
    }
  }
  if (state.lease && historyIncludes(view, state.lease.commit)) state.lease = null;
}

function blocked(state, reason, retryAt) {
  const result = {ok: false, enabled: state.enabled, reason};
  if (retryAt != null) result.retryAt = retryAt;
  return result;
}

function status(state) {
  const pending = state.attempts.find(unresolved);
  return {ok: true, enabled: state.enabled, cutoff: CUTOFF, repository: REPOSITORY,
    pendingCommit: pending?.commit || null, reservedCommit: state.lease?.commit || null, anchors: anchors(state),
    reason: pending ? "Waiting for the previous commit to appear in team history." :
      state.enabled ? "Monitoring the team practice form." : "Practice helper stopped."};
}

function gate(state, view, now) {
  if (now >= CUTOFF) return blocked(state, "The practice deadline has passed.");
  if (!state.enabled) return blocked(state, "Practice helper stopped.");
  if (!validView(view) || !sameTeam(state, view)) return blocked(state, "Waiting for verified GTGoats submission history.");
  if (state.attempts.some(unresolved)) {
    return blocked(state, "Waiting for the previous commit to appear in team history.");
  }
  if (view.queued) return blocked(state, "The team already has a queued submission.");
  if (view.remaining === 0 || view.retryAt > now) {
    return blocked(state, "Waiting for the site's submission quota.", view.retryAt > now ? view.retryAt : undefined);
  }
  const recent = [...state.attempts, ...(view.remaining === null ? state.manual || [] : [])]
    .map(a => a.at).filter(at => at > now - HOUR).sort((a, b) => a - b);
  let next = recent.length ? recent[recent.length - 1] + GAP : 0;
  if (recent.length >= 4) next = Math.max(next, recent[recent.length - 4] + HOUR + 1000);
  if (view.remaining === null) next = Math.max(next, state.startedAt + HOUR + 1000);
  if (now < next) return blocked(state, "Waiting for the next local submission slot.", next);
  return null;
}

function reservationResult(lease) {
  return {ok: true, enabled: true, repository: REPOSITORY, commit: lease.commit, token: lease.token};
}

function chooseCandidate(state, queue) {
  const tried = new Set([...ORIGINAL, ...state.attempts.map(a => a.commit)]);
  const eligible = queue.filter(c => !tried.has(c.commit) && !state.seen.some(p => matches(c.commit, p)));
  if (state.lease) return eligible.find(c => c.commit === state.lease.commit)?.commit;
  if (!eligible.length || (state.attempts.length + 1) % 4 === 0) return eligible[0]?.commit;
  const scores = new Map(ORIGINAL.map((sha, i) => [sha, INITIAL_SCORES[i]]));
  for (const r of state.results || []) {
    if (Number.isFinite(r.score) && r.status.startsWith("Scored")) scores.set(r.commit, r.score);
  }
  let choice = eligible[0];
  let best = -Infinity;
  for (const candidate of eligible) {
    const score = Math.max(-Infinity, ...candidate.parents.map(p => scores.get(p) ?? -Infinity));
    if (score > best) {
      choice = candidate;
      best = score;
    }
  }
  return choice.commit;
}

async function handle(msg, tabId) {
  const state = await loadState();
  let now = Date.now();
  const expired = now >= CUTOFF;
  if (expired) state.enabled = false;
  if (state.lease && (now >= state.lease.expires || expired)) state.lease = null;
  if (!state.tabs.includes(tabId)) state.tabs = [...state.tabs.slice(-11), tabId];
  const view = msg.view;
  if (validView(view) && sameTeam(state, view)) reconcile(state, view, now);
  // Always persist reconciliation, even when a request is ultimately denied.
  await save(state);

  if (msg.type === "status") return status(state);
  if (msg.type === "export") {
    return {ok: true, schema: 1, repository: REPOSITORY, results: state.results || [],
      attempts: state.attempts.map(({commit, at, status, confirmedAt, retiredAt}) =>
        ({commit, at, status, confirmedAt, retiredAt}))};
  }
  if (msg.type === "resolve") {
    const attempt = state.attempts.find(a => a.commit === msg.commit && unresolved(a));
    if (state.enabled || !attempt || msg.attested !== true || msg.team !== "GT Goats" ||
        !validView(view) || !sameTeam(state, view) || view.queued || historyIncludes(view, attempt.commit)) {
      return blocked(state, "Stop the helper and verify the missing commit against an idle team history.");
    }
    // Keep the original quota timestamp and permanently exclude this SHA.
    // A subsequently visible official receipt still reconciles normally.
    attempt.status = "retired";
    attempt.retiredAt = now;
    await save(state);
    return status(state);
  }
  if (msg.type === "start" || msg.type === "stop") {
    if (msg.type === "start" && expired) return blocked(state, "The practice deadline has passed.");
    if (msg.type === "start" && (msg.team !== "GT Goats" || msg.attested !== true ||
        !validView(view) || !sameTeam(state, view))) {
      return blocked(state, "Use Start on the verified GTGoats team history.");
    }
    if (!state.enabled && msg.type === "start") state.startedAt = now;
    state.enabled = msg.type === "start";
    if (!state.enabled) state.lease = null;
    await save(state);
    if (state.enabled) await chrome.alarms.create(ALARM, {periodInMinutes: 1});
    else await chrome.alarms.clear(ALARM);
    return status(state);
  }
  if (msg.type === "release") {
    if (state.lease?.token !== msg.token || state.lease?.tabId !== tabId) {
      return blocked(state, "No matching unspent reservation.");
    }
    state.lease = null;
    await save(state);
    return status(state);
  }
  if (msg.type === "complete" || msg.type === "uncertain") {
    const attempt = state.attempts.find(a => a.token === msg.token && a.tabId === tabId);
    if (!attempt) return blocked(state, "No matching dispatched attempt.");
    if (!unresolved(attempt)) return status(state);
    if (msg.type === "uncertain") {
      attempt.status = "uncertain";
      await save(state);
    }
    return blocked(state, "Waiting for confirmation in visible team history.");
  }
  if (!["claim", "dispatch"].includes(msg.type)) return blocked(state, "Unknown practice helper request.");
  const denied = gate(state, view, now);
  if (denied) return denied;

  if (msg.type === "dispatch" && (!state.lease || state.lease.tabId !== tabId || state.lease.token !== msg.token)) {
    return blocked(state, "No matching unspent reservation.");
  }
  if (state.lease && state.lease.tabId !== tabId) {
    return blocked(state, "Another track tab has the current reservation.", state.lease.expires);
  }
  let queue;
  try {
    queue = await candidates(msg.type === "dispatch");
  } catch {
    return blocked(state, "Waiting for a valid public candidate queue.");
  }
  state.knownQueue = [...new Set([...(state.knownQueue || []), ...queue.flatMap(c => [c.commit, ...c.parents])])].slice(-2048);
  reconcile(state, view, Date.now());
  now = Date.now();
  if (now >= CUTOFF || (state.lease && now >= state.lease.expires)) {
    state.lease = null;
    if (now >= CUTOFF) state.enabled = false;
    await save(state);
    return blocked(state, now >= CUTOFF ? "The practice deadline has passed." : "The reservation expired.");
  }
  const next = chooseCandidate(state, queue);
  if (!next) {
    const withdrawn = Boolean(state.lease);
    state.lease = null;
    await save(state);
    return blocked(state, withdrawn ? "The queue changed. Refresh the reservation." : "Waiting for a new tested candidate.");
  }
  if (msg.type === "claim") {
    if (!state.lease) {
      state.lease = {token: crypto.randomUUID(), tabId, commit: next, expires: now + LEASE_MS};
      await save(state);
    }
    return reservationResult(state.lease);
  }

  const lease = state.lease;
  state.attempts.push({commit: lease.commit, token: lease.token, tabId, at: now, status: "dispatched"});
  state.lease = null;
  await save(state);
  return reservationResult(lease);
}

chrome.runtime.onMessage.addListener((msg, sender, respond) => {
  if (!allowedSender(sender) || !msg || typeof msg.type !== "string") return false;
  serialized(() => handle(msg, sender.tab.id)).then(respond, () => {
    respond({ok: false, enabled: false, reason: "Practice storage or scheduling is unavailable."});
  });
  return true;
});

async function wake() {
  const state = await loadState();
  if (!state.enabled || Date.now() >= CUTOFF) {
    state.enabled = false;
    state.lease = null;
    await save(state);
    await chrome.alarms.clear(ALARM);
    return;
  }
  // A tab ID is registered only after a message from the pinned track page.
  // A failed send can indicate a closed, sleeping or newly navigated tab.
  for (const id of state.tabs) chrome.tabs.sendMessage(id, {type: "wake"}).catch(() => {});
}

chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name === ALARM) serialized(wake).catch(() => {});
});
chrome.runtime.onStartup.addListener(() => {
  serialized(async () => {
    const state = await loadState();
    if (state.enabled && Date.now() < CUTOFF) await chrome.alarms.create(ALARM, {periodInMinutes: 1});
    else if (state.enabled) await wake();
  }).catch(() => {});
});
