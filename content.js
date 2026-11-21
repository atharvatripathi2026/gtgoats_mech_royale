// Operates only the team's ordinary practice form in the top-level Builders track page.
(() => {
  "use strict";
  const ORIGIN = "https://www.joinbuilders.org";
  const TRACK = "/buildathon/tracks/builders";
  const REPO = "https://github.com/atharvatripathi2026/gtgoats_mech_royale";
  const CUTOFF = Date.parse("2026-11-22T16:00:00Z");
  const PANEL_ID = "gt-goats-practice-helper";
  const VERIFIED = new Map([
    ["BB-073A1E2D", "4cb4a9ea753e8df3744a9ba8d44053068e64e535"],
    ["BB-C6067CA3", "9e59bbfd46f562dbb88d0a4377dc333ce2f8c273"],
  ]);
  const STATUSES = new Set(["Queued", "Scoring", "Scored", "Scored under a previous version",
    "Rejected", "Scoring problem"]);
  const clean = el => (el?.textContent || "").replace(/\s+/g, " ").trim();
  function visible(el) {
    if (!el?.isConnected || el.closest('[hidden], [inert], [aria-hidden="true"]')) return false;
    const style = el.ownerDocument.defaultView.getComputedStyle(el);
    return style.visibility !== "hidden" && style.visibility !== "collapse" && el.getClientRects().length > 0;
  }
  function unique(nodes) {
    const matches = [...nodes].filter(visible);
    return matches.length === 1 ? matches[0] : null;
  }
  function practiceFields(form) {
    if (!form || !visible(form)) return null;
    const repo = unique(form.querySelectorAll('input[name="repo"][type="url"]'));
    const commit = unique(form.querySelectorAll('input[name="commit"]'));
    const buttons = [...form.querySelectorAll("button")].filter(b => b.form === form &&
      b.type === "submit" && ["Submit", "Submitting", "Paused"].includes(clean(b)));
    const button = unique(buttons);
    if (!repo || !commit || !button || ![...repo.labels].some(l => clean(l).includes("Public GitHub repository"))
        || ![...commit.labels].some(l => clean(l).includes("Commit (optional)"))) return null;
    return {repo, commit, button};
  }
  function readView(doc, anchors = []) {
    const verified = new Map(VERIFIED);
    for (const anchor of Array.isArray(anchors) ? anchors : []) {
      if (/^BB-[A-Z0-9]+$/.test(anchor?.receipt) && /^[a-f0-9]{40}$/.test(anchor?.commit)) {
        verified.set(anchor.receipt, anchor.commit);
      }
    }
    const base = {historyReady: false, identityVerified: false, queued: false, remaining: null,
      commits: [], receipts: [], form: null, ready: false, reason: "Waiting for the signed-in practice form."};
    const area = doc.getElementById("submit");
    if (!area) return base;
    const subheading = unique([...area.querySelectorAll("section h3")]
      .filter(h => clean(h) === "Your team's submissions"));
    const history = subheading?.closest("section");
    if (!history) return base;
    const lists = [...history.querySelectorAll(":scope > ol")].filter(visible);
    if (lists.length !== 1) return {...base, reason: "Waiting for the team's submission history."};
    const cards = [...lists[0].children].filter(visible);
    if (!cards.length) return base;
    for (const card of cards) {
      const spans = card.querySelector(":scope > div")?.querySelectorAll(":scope > span");
      const receipt = clean(spans?.[0]), status = clean(spans?.[1]);
      if (card.tagName !== "LI" || !visible(spans?.[0]) || !visible(spans?.[1]) ||
          !/^BB-[A-Z0-9]+$/.test(receipt) || !STATUSES.has(status)) {
        return {...base, historyReady: false, reason: "Waiting for a recognizable submission history."};
      }
      if (status === "Queued" || status === "Scoring") base.queued = true;
      const meta = [...card.querySelectorAll(":scope > p")].filter(visible).map(clean)
        .map(t => /^(https:\/\/github\.com\/[\w.-]+\/[\w.-]+)\s+@\s+([a-fA-F0-9]{12,40})$/.exec(t))
        .find(m => m && m[1] === REPO);
      if (!meta) continue;
      const commit = meta[2].toLowerCase();
      const scoreText = spans.length > 3 ? clean(spans[2]) : "";
      const score = /^-?\d+(?:\.\d+)?(?:\s+(?:points?|pts))?$/i.test(scoreText) ? Number.parseFloat(scoreText) : null;
      const message = (card.querySelector(":scope > p.break-words.whitespace-pre-wrap")?.textContent || "").trim().slice(0, 3000);
      base.receipts.push({receipt, status, commit, score, message});
      base.commits.push(commit);
      if (verified.get(receipt)?.startsWith(commit)) base.identityVerified = true;
    }
    base.historyReady = true;
    if (!base.identityVerified) return {...base, reason: "Waiting for a verified GT Goats receipt in this team's history."};
    const form = unique([...area.querySelectorAll("form")]
      .filter(f => [...f.querySelectorAll("h3")].some(h => visible(h) && clean(h) === "Submit")));
    base.form = form;
    const fields = practiceFields(form);
    if (!fields) return base;
    const quota = /^([0-4]) of 4 left this hour$/;
    const counters = [...form.querySelectorAll("span"), ...area.querySelectorAll('section[aria-label="Your hour and the queue"] span')]
      .filter(visible).map(el => quota.exec(clean(el))).filter(Boolean).map(m => Number(m[1]));
    if (!counters.length || counters.some(value => value !== counters[0])) {
      return {...base, reason: "Waiting for the hourly allowance."};
    }
    base.remaining = counters[0];
    if (base.queued) base.reason = "Waiting for the team's current run to finish.";
    else if (!base.remaining) base.reason = "Waiting for the next hourly slot.";
    else if (clean(fields.button) !== "Submit" || fields.button.matches(":disabled") ||
             fields.button.getAttribute("aria-disabled") === "true" ||
             fields.repo.matches(":disabled") || fields.commit.matches(":disabled")) {
      base.reason = "Waiting for the practice form to open.";
    } else {
      base.ready = true;
      base.reason = "Practice form ready.";
    }
    return base;
  }
  function fillForm(form, repository, commit) {
    if (repository !== REPO || !/^[a-f0-9]{40}$/.test(commit)) return false;
    const fields = practiceFields(form);
    if (!fields || clean(fields.button) !== "Submit" || fields.button.matches(":disabled")) return false;
    if ((fields.repo.value && fields.repo.value !== repository) ||
        (fields.commit.value && fields.commit.value !== commit)) return false;
    const win = form.ownerDocument.defaultView;
    const setValue = Object.getOwnPropertyDescriptor(win.HTMLInputElement.prototype, "value").set;
    for (const [field, value] of [[fields.repo, repository], [fields.commit, commit]]) {
      setValue.call(field, value);
      field.dispatchEvent(new win.Event("input", {bubbles: true}));
      field.dispatchEvent(new win.Event("change", {bubbles: true}));
    }
    return fields.repo.value === repository && fields.commit.value === commit && form.checkValidity();
  }
  function workerView(view) {
    return {historyReady: view.historyReady, identityVerified: view.identityVerified, queued: view.queued,
      remaining: view.remaining, commits: view.commits, receipts: view.receipts, team: "GT Goats"};
  }
  function present() {
    return window === window.top && location.origin === ORIGIN &&
      location.pathname.replace(/\/$/, "") === TRACK;
  }
  function downloadResults(data, format, doc) {
    if (!data?.ok || !Array.isArray(data.results)) return false;
    const attempts = Array.isArray(data.attempts) ? data.attempts : [];
    let body, mime;
    if (format === "csv") {
      const columns = ["commit", "receipt", "status", "score", "message"];
      const rows = [...data.results, ...attempts.filter(a => !data.results.some(r => r.commit === a.commit))];
      function cell(value) {
        let content = String(value ?? "");
        if (/^[\s]*[=+@-]/.test(content)) content = "'" + content;
        return '"' + content.replace(/"/g, '""') + '"';
      }
      body = [columns, ...rows.map(r => columns.map(k => r[k]))].map(row => row.map(cell).join(",")).join("\r\n");
      mime = "text/csv;charset=utf-8";
    } else {
      body = JSON.stringify({repository: data.repository, exportedAt: new Date().toISOString(),
        results: data.results, attempts}, null, 2);
      mime = "application/json";
    }
    const win = doc.defaultView;
    const url = win.URL.createObjectURL(new win.Blob([body], {type: mime}));
    const link = doc.createElement("a");
    link.href = url;
    link.download = "gt-goats-practice-" + new Date().toISOString().slice(0, 10) + "." + format;
    doc.body.append(link); link.click(); link.remove();
    win.setTimeout(() => win.URL.revokeObjectURL(url), 10000);
    return true;
  }
  function mount() {
    if (!present() || document.getElementById(PANEL_ID)) return;
    const panel = document.createElement("aside");
    panel.id = PANEL_ID;
    const ui = panel.attachShadow({mode: "open"});
    ui.innerHTML = `<style>
      :host{position:fixed;bottom:14px;right:14px;z-index:2147483646;max-width:min(286px,92vw);font:14px/1.4 system-ui,sans-serif;color:#172033;}
      section{padding:13px 15px;border-radius:12px;border:1px solid #bac6d8;background:#fff;box-shadow:0 3px 18px #14223c26}
      strong{font-size:15px} p{margin:7px 0} button{font:inherit;cursor:pointer;padding:6px 10px;color:#fff;background:#254570;border:0;border-radius:5px}
      button:disabled{cursor:default;opacity:.55} [hidden]{display:none}
    </style><section aria-label="GT Goats practice helper"><strong>GT Goats practice</strong>
      <p role="status" aria-live="polite">Checking this team's practice form.</p>
      <p id="attestation">Starting confirms you are signed in for GT Goats and authorizes this browser to submit practice entries until the cutoff.</p>
      <button type="button" id="start" disabled>Start GT Goats submissions</button>
      <button type="button" id="stop" hidden>Stop</button>
      <p><select id="format" aria-label="Result format"><option>JSON</option><option>CSV</option></select>
        <button type="button" id="export">Export results</button></p>
      <div id="recovery" hidden><p id="recovery-text"></p><button type="button" id="resolve">Retire unconfirmed commit</button></div></section>`;
    document.body.append(panel);
    const start = ui.getElementById("start"), stop = ui.getElementById("stop");
    const say = message => { ui.querySelector('[role="status"]').textContent = message; };
    const send = message => chrome.runtime.sendMessage(message);
    let enabled = false, busy = false, stopped = false, generation = 0;
    let pending = null, reloadNeeded = false, anchors = [], unresolved = null, owned = null;
    const startedAt = Date.now();
    function draw(isEnabled, view) {
      enabled = isEnabled;
      start.hidden = isEnabled;
      start.disabled = !view.identityVerified || !view.form || Date.now() >= CUTOFF;
      stop.hidden = !isEnabled;
      ui.getElementById("attestation").hidden = isEnabled;
      const recover = !isEnabled && unresolved && view.identityVerified && !view.queued &&
        !view.commits.some(sha => unresolved.startsWith(sha));
      ui.getElementById("recovery").hidden = !recover;
      if (recover) ui.getElementById("recovery-text").textContent =
        "After checking team history, retire " + unresolved + " to skip that commit permanently.";
    }
    const active = g => present() && !stopped && g === generation && Date.now() < CUTOFF;
    const same = (grant, claim) => grant?.ok && grant.repository === REPO &&
      grant.token === claim.token && grant.commit === claim.commit && /^[a-f0-9]{40}$/.test(grant.commit);
    function fresh() {
      return Date.now() - startedAt < 90000 && !reloadNeeded;
    }
    function ownedDraft(form) {
      const fields = practiceFields(form);
      if (!fields || form.contains(document.activeElement) || fields.repo.value !== REPO) return false;
      const commit = fields.commit.value;
      return commit && (commit === owned || commit === unresolved || anchors.some(a => a.commit === commit));
    }
    function cleanDraft(form) {
      const fields = practiceFields(form);
      return Boolean(fields && !form.contains(document.activeElement) &&
        ((!fields.repo.value || fields.repo.value === REPO) && !fields.commit.value || ownedDraft(form)));
    }
    function clearOwned(form) {
      if (!ownedDraft(form)) return;
      const fields = practiceFields(form);
      for (const field of [fields.repo, fields.commit]) {
        field.value = "";
        field.dispatchEvent(new Event("input", {bubbles: true}));
        field.dispatchEvent(new Event("change", {bubbles: true}));
      }
      owned = null;
    }
    async function tick() {
      // A Next.js route transition can keep the same content-script context alive.
      panel.hidden = !present();
      if (busy || panel.hidden) return;
      busy = true;
      const g = generation;
      try {
        const state = await send({type: "status"});
        if (g !== generation || !present()) return;
        anchors = Array.isArray(state?.anchors) ? state.anchors : [];
        unresolved = /^[a-f0-9]{40}$/.test(state?.pendingCommit) ? state.pendingCommit : null;
        const view = readView(document, anchors);
        draw(Boolean(state?.enabled), view);
        if (Date.now() >= CUTOFF) {
          if (enabled) await send({type: "stop"});
          draw(false, view); say("Practice submissions are closed."); return;
        }
        if (!enabled || stopped) { say(view.identityVerified ? "Practice automation is stopped." : view.reason); return; }
        if (!view.identityVerified) { say(view.reason); return; }
        if (pending) {
          const receipt = view.receipts.find(row => pending.commit.startsWith(row.commit));
          if (receipt) {
            const result = await send({type: "complete", token: pending.token, view: workerView(view)});
            if (result?.ok) { clearOwned(view.form); say("Recorded receipt " + receipt.receipt + "."); pending = null; }
          } else {
            say("Waiting for the submitted commit to appear in the team's history.");
            if (Date.now() - pending.time > 90000 && cleanDraft(view.form)) location.reload();
          }
          return;
        }
        // The worker reconciles receipts even while a scored run is in progress.
        const request = await send({type: "claim", view: workerView(view)});
        if (!request?.ok || !request.token) {
          // Builders refreshes its own polling view only in visible tabs. A
          // background tab must reload periodically even at zero remaining.
          if (active(g) && !fresh() && cleanDraft(view.form)) { location.reload(); return; }
          say(!view.ready ? view.reason : String(request?.reason || "Waiting for the next verified candidate."));
          return;
        }
        const token = request.token, commit = request.commit;
        const release = () => send({type: "release", token});
        if (!active(g) || !view.ready || request.repository !== REPO || !/^[a-f0-9]{40}$/.test(commit)) {
          await release(); return;
        }
        if (!fresh()) {
          await release();
          if (active(g) && cleanDraft(view.form)) location.reload();
          else say("Waiting for the current draft before refreshing the form.");
          return;
        }
        const before = readView(document, anchors);
        clearOwned(before.form);
        if (!before.ready || !before.identityVerified || before.commits.some(v => commit.startsWith(v)) ||
            !fillForm(before.form, REPO, commit)) {
          await release(); say("Waiting for a clear, eligible practice form."); return;
        }
        // The worker spends this slot durably before the click; an ambiguous receipt
        // must be reconciled from visible history before another attempt is possible.
        owned = commit;
        const grant = await send({type: "dispatch", token, view: workerView(before)});
        if (!grant?.ok) { clearOwned(before.form); say(String(grant?.reason || "The reserved slot expired.")); return; }
        pending = {token, commit, time: Date.now()};
        const current = readView(document, anchors), fields = practiceFields(current.form);
        if (!active(g) || !same(grant, request) || !current.ready || !current.identityVerified ||
            current.form !== before.form || current.commits.some(v => commit.startsWith(v)) ||
            !fields || fields.repo.value !== REPO || fields.commit.value !== commit || !current.form.checkValidity()) {
          await send({type: "uncertain", token}); say("Reservation changed. Checking team history."); return;
        }
        fields.button.click();
        say("Submitted " + commit.slice(0, 12) + ". Waiting for the team receipt.");
        setTimeout(tick, 1800);
      } catch (error) {
        if (pending) await send({type: "uncertain", token: pending.token}).catch(() => {});
        say("Helper paused while reconnecting to the browser extension.");
      } finally {
        busy = false;
      }
    }
    start.addEventListener("click", async event => {
      if (!event.isTrusted || !present() || Date.now() >= CUTOFF) return;
      const view = readView(document, anchors);
      if (!view.identityVerified || !view.form) { say(view.reason); return; }
      start.disabled = true;
      const g = ++generation;
      try {
        const result = await send({type: "start", attested: true, team: "GT Goats", view: workerView(view)});
        if (g !== generation) return;
        stopped = false;
        draw(Boolean(result?.enabled), view);
        say(result?.ok ? "Practice automation started." : String(result?.reason || "Start was declined."));
        if (result?.ok) setTimeout(tick, 0);
      } catch { start.disabled = false; say("Could not start the practice helper."); }
    });
    stop.addEventListener("click", async event => {
      if (!event.isTrusted) return;
      stopped = true; generation++;
      try {
        const result = await send({type: "stop"});
        if (result?.ok) stopped = false;
        draw(Boolean(result?.enabled), readView(document, anchors));
        say(result?.ok ? "Practice automation stopped." : "Waiting for stop confirmation.");
      } catch { say("This tab is stopped. Waiting for the extension to confirm."); }
    });
    ui.getElementById("export").addEventListener("click", async e => {
      if (!e.isTrusted || !present()) return;
      try {
        const data = await send({type: "export", view: workerView(readView(document, anchors))});
        if (downloadResults(data, ui.getElementById("format").value.toLowerCase(), document)) say("Saved the local practice results.");
        else say("Practice results are unavailable.");
      } catch { say("Could not export practice results."); }
    });
    ui.getElementById("resolve").addEventListener("click", async e => {
      if (!e.isTrusted || !present() || enabled || !unresolved) return;
      const view = readView(document, anchors);
      if (!view.identityVerified || view.queued || view.commits.some(sha => unresolved.startsWith(sha))) return;
      try {
        const result = await send({type: "resolve", commit: unresolved, team: "GT Goats", attested: true, view: workerView(view)});
        if (result?.ok) { pending = null; clearOwned(view.form); unresolved = null; }
        say(result?.ok ? "Permanently retired the unconfirmed commit." : String(result?.reason || "Could not retire this commit."));
        draw(false, view);
      } catch { say("Could not retire this commit."); }
    });
    chrome.runtime.onMessage.addListener(message => {
      if (message?.type === "wake") { void tick(); }
    });
    window.addEventListener("pageshow", e => { if (e.persisted) { reloadNeeded = true; void tick(); } });
    window.addEventListener("focus", () => void tick());
    window.addEventListener("popstate", () => void tick());
    setInterval(tick, 15000);
    void tick();
  }

  if (typeof module === "object" && module.exports) module.exports = {readView, fillForm, workerView, practiceFields, downloadResults};
  if (typeof chrome !== "undefined" && chrome.runtime?.id && typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, {once: true});
    else mount();
  }
})();
