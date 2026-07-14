// Career OS Agent — Single Job Mode ONLY.
// Applies to the ONE job visible on screen. Fills the form step by step.
// After "Submit application" → STOPS. User clicks "Apply" again for the next job.
(function () {
  const COS = window.COS;
  const CFG = COS.CONFIG;
  const { State, Scanner, Executor, Widget } = COS;

  let loopHandle = null;
  let paused = false;
  let pendingUserInput = null;
  let ticking = false;  // LOCK: prevents overlapping ticks

  // Error tracking
  let consecutiveErrors = 0;
  const MAX_ERRORS = 5;
  let stepCount = 0;

  function log(msg) {
    console.log(`%c[CareerOS] ${msg}`, "color: #3b82f6; font-weight: bold");
  }

  // ---- Lifecycle ----

  async function init() {
    Widget.mount({ onStart: start, onStop: stop, onHandoffResolve: resolveHandoff });
    const s = await State.load();
    if (s && s.running) {
      log("Found running session, resuming...");
      Widget.setRunning(true);
      Widget.status("Resuming…");
      scheduleNext(CFG.SETTLE_MS);
    } else {
      // Load quota info for the status display
      try {
        const usageRes = await chrome.runtime.sendMessage({ kind: "USAGE" });
        if (usageRes && usageRes.ok) {
          const u = usageRes.data;
          Widget.showQuotaInfo(u.count, u.limit_val, u.tier);
        } else {
          Widget.status("Ready — open a job and click Apply");
        }
      } catch (_) {
        Widget.status("Ready — start the backend server first");
      }
    }
  }

  async function start() {
    log("User clicked Apply — starting single job application");

    // Check quota before starting
    try {
      const usageRes = await chrome.runtime.sendMessage({ kind: "USAGE" });
      if (usageRes && usageRes.ok) {
        const u = usageRes.data;
        if (u.count >= u.limit_val) {
          log(`Quota exhausted: ${u.count}/${u.limit_val} (${u.tier})`);
          Widget.showUpgradePrompt(
            `You've used all ${u.limit_val} free applications this month (${u.count}/${u.limit_val}). Upgrade to Pro for ₹11/month to get 50 applications!`
          );
          return; // Don't start
        }
        Widget.showQuotaInfo(u.count, u.limit_val, u.tier);
      }
    } catch (e) {
      log("Quota check failed, proceeding anyway: " + e);
    }

    await State.start("apply");
    Widget.setRunning(true);
    Widget.status("Starting…");
    stepCount = 0;
    consecutiveErrors = 0;
    ticking = false;
    scheduleNext(CFG.SETTLE_MS);
  }

  async function stop() {
    log("Agent STOPPED");
    if (loopHandle) {
      clearTimeout(loopHandle);
      loopHandle = null;
    }
    ticking = false;
    await State.stop();
    Widget.setRunning(false);
    Widget.status("Ready — open a job and click Apply");
  }

  function scheduleNext(ms) {
    if (loopHandle) clearTimeout(loopHandle);
    loopHandle = null;
    if (State.isRunning() && !paused) {
      loopHandle = setTimeout(tick, ms);
    }
  }

  // ---- The main loop: ONE tick = ONE planner step ----

  async function tick() {
    // LOCK: if already ticking, skip
    if (ticking) {
      log("Tick skipped — previous tick still running");
      return;
    }
    if (!State.isRunning() || paused) return;

    ticking = true;
    loopHandle = null;

    try {
      await doOneStep();
    } catch (err) {
      if (String(err).includes('Extension context invalidated')) {
        document.body.insertAdjacentHTML('beforeend', 
          '<div style="position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:2147483647;background:#ef4444;color:white;padding:16px 24px;border-radius:12px;font-family:sans-serif;font-size:14px;box-shadow:0 4px 24px rgba(0,0,0,0.3)">Career OS: Extension updated. Please refresh this page (F5) to continue.</div>');
        return;
      }
      log("Unexpected error in tick: " + err);
      Widget.status("Error: " + String(err).slice(0, 40));
    } finally {
      ticking = false;
    }
  }

  async function doOneStep() {
    // --- 1. PERCEIVE: scan the visible page ---
    const all = Scanner.scan();
    
    // Check for CAPTCHA challenges
    const captchaFrame = document.querySelector('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="challenges.cloudflare"], iframe[title*="reCAPTCHA"]');
    if (captchaFrame) {
      log('CAPTCHA detected — pausing for human');
      paused = true;
      Widget.requestHandoff({ type: 'ask_user', prompt: 'A CAPTCHA challenge was detected. Please solve it, then click Resume.', input_kind: 'manual' });
      return;
    }
    
    // Check if job posting is closed
    if (Scanner.isJobClosed()) {
      log('Job closed detected — stopping');
      Widget.status('This job is no longer accepting applications.');
      await stop();
      return;
    }
    
    const prev = State.session.prevElements || [];
    const elements = Scanner.diff(all, prev);
    const stageHash = Scanner.stageHash(all);

    stepCount++;
    log(`Step ${stepCount}: scanned ${all.length} elements, sending ${elements.length} to backend`);

    const payload = {
      session_id: State.session.id,
      url: location.href,
      title: document.title,
      elements,
      total_elements: all.length,
      stage_hash: stageHash,
      user_input: pendingUserInput,
      objective: State.session.objective,
    };
    pendingUserInput = null;
    State.session.prevElements = all;
    State.session.lastStageHash = stageHash;
    await State.save();

    Widget.status(`Step ${stepCount}`, "thinking…");

    // --- 2. THINK: ask the backend ---
    let resp;
    try {
      const r = await chrome.runtime.sendMessage({ kind: "STEP", payload });
      if (!r || !r.ok) throw new Error(r?.error || "no response from backend");
      resp = r.data;
      consecutiveErrors = 0;
    } catch (e) {
      consecutiveErrors++;
      log(`Backend error #${consecutiveErrors}: ${e}`);
      Widget.status(`Backend error (${consecutiveErrors}/${MAX_ERRORS})`, String(e).slice(0, 50));

      if (consecutiveErrors >= MAX_ERRORS) {
        Widget.status('Multiple errors — paused. Fill this step manually, then click Resume.');
        paused = true;
        Widget.requestHandoff({ type: 'ask_user', prompt: 'Too many backend errors. Please fill this step manually and click Resume.', input_kind: 'manual' });
        return;
      }
      const delay = Math.min(2000 * Math.pow(2, consecutiveErrors), 30000);
      scheduleNext(delay);
      return;
    }

    log(`Backend replied: source=${resp.source}, actions=${resp.script.length}`);
    Widget.status(resp.reason || resp.stage || "working", resp.source);

    // --- 3. ACT: execute actions one by one ---
    for (let i = 0; i < resp.script.length; i++) {
      const action = resp.script[i];
      log(`  Action ${i + 1}/${resp.script.length}: ${action.type} → ${action.target_id || "(no target)"}`);

      const result = await Executor.runAction(action);

      // --- HANDOFF: pause for user ---
      if (result.control === "ask_user") {
        log("  → Pausing for user input");
        paused = true;
        Widget.requestHandoff(action);
        return; // stops the loop; resolveHandoff() resumes it
      }

      // --- DONE: application submitted → STOP ---
      if (result.control === "done") {
        log("  → ✅ APPLICATION SUBMITTED — STOPPING AGENT");
        Widget.status("✅ Application submitted!");
        await stop();
        return; // FULLY STOPPED. No more ticks.
      }

      // --- ABORT ---
      if (result.control === "abort") {
        log("  → Aborted by backend");
        Widget.status("Aborted");
        await stop();
        return;
      }

      // Human-like delay between each action
      const delay = COS.rand(CFG.MIN_ACTION_DELAY_MS, CFG.MAX_ACTION_DELAY_MS);
      log(`  → Waiting ${delay}ms before next action`);
      await COS.sleep(delay);
    }

    // Check if we just clicked a submit/next button — add cooldown
    const clickedSubmit = resp.script.some(a => a.type === 'click' && (a.submit || a.next));
    if (clickedSubmit) {
      log('Post-submit cooldown: waiting for page change...');
      await COS.sleep(2000); // Wait for navigation
    }

    // Schedule the next tick (next perceive-think-act cycle)
    log(`Step ${stepCount} complete. Next tick in ${CFG.SETTLE_MS}ms`);
    scheduleNext(CFG.SETTLE_MS);
  }

  // ---- Handoff: user provided input ----

  async function resolveHandoff(payload, action) {
    if (payload.cancelled) {
      Widget.status("Paused — press Stop or continue manually");
      return;
    }
    if (payload.confirmed_submit && action.target_id) {
      const el = Scanner.resolve(action.target_id);
      if (el) {
        log("User confirmed submit — clicking submit button");
        Executor.clickEl(el);
      }
    }
    pendingUserInput = payload;
    paused = false;
    log("User resolved handoff — resuming");
    Widget.status("Resuming…");
    scheduleNext(CFG.SETTLE_MS);
  }

  // ---- Boot ----
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
