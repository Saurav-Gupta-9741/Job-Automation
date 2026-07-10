// The orchestrator: Perceive (scan) -> Think (backend) -> Act (execute), with human-like
// pacing, handoff pauses, and resume-after-redirect. One loop iteration == one planner step.
(function () {
  const COS = window.COS;
  const CFG = COS.CONFIG;
  const { State, Scanner, Executor, Widget } = COS;

  let loopHandle = null;
  let paused = false;          // true while waiting on a human handoff
  let pendingUserInput = null; // delivered to the next step after a handoff resolves
  let manualChanges = {};      // tracks fields the user manually interacted with during a pause

  // Enhanced error recovery with exponential backoff
  let consecutiveErrors = 0;
  const MAX_CONSECUTIVE_ERRORS = 5;
  const BASE_RETRY_DELAY = 2000; // 2 seconds
  const MAX_RETRY_DELAY = 30000; // 30 seconds

  // Progress tracking for multi-step applications
  let stageHistory = [];
  let stepCount = 0;

  function getRetryDelay() {
    const delay = Math.min(
      BASE_RETRY_DELAY * Math.pow(2, consecutiveErrors),
      MAX_RETRY_DELAY
    );
    return delay;
  }
  
  function updateProgress(currentHash) {
    if (currentHash && !stageHistory.includes(currentHash)) {
      stageHistory.push(currentHash);
      stepCount++;
    }
    if (stepCount > 0) {
      Widget.status(`Step ${stepCount}`, 'working');
    }
  }

  async function init() {
    Widget.mount({ onStart: start, onStop: stop, onHandoffResolve: resolveHandoff });
    const s = await State.load();
    
    if (s && s.running) {
      // Check if session is stale (>30 minutes old)
      const sessionTimestamp = parseInt(s.id.split('-')[1], 36);
      const sessionAge = Date.now() - sessionTimestamp;
      const THIRTY_MINUTES = 30 * 60 * 1000;
      
      if (sessionAge > THIRTY_MINUTES) {
        // Stale session - ask user if they want to resume
        Widget.showRecoveryDialog(
          "Found incomplete application from " + new Date(sessionTimestamp).toLocaleTimeString() + ". Resume?",
          async () => {
            Widget.setRunning(true);
            Widget.status("Resuming previous session…");
            startLoop();
          },
          async () => {
            await State.stop();
            Widget.status("Idle");
          }
        );
      } else {
        // Recent session - auto-resume
        Widget.setRunning(true);
        Widget.status("Resuming…");
        startLoop();
      }
    } else {
      Widget.status("Idle");
    }
  }

  async function start() {
    await State.start("apply");
    Widget.setRunning(true);
    Widget.status("Starting…");
    stageHistory = [];
    stepCount = 0;
    startLoop();
  }

  async function stop() {
    stopLoop();
    await State.stop();
    Widget.setRunning(false);
    Widget.status("Stopped");
  }

  function startLoop() {
    if (loopHandle) return;
    loopHandle = setTimeout(tick, CFG.SETTLE_MS);
  }

  function stopLoop() {
    if (loopHandle) clearTimeout(loopHandle);
    loopHandle = null;
  }

  async function moveToNextJob() {
    Widget.status("Moving to next job...");
    await COS.sleep(1500);

    // 1. Close the success modal if it exists
    const dismissBtn = document.querySelector('button[aria-label="Dismiss"]') || 
                       Array.from(document.querySelectorAll('button')).find(b => {
                         const txt = (b.innerText || "").toLowerCase();
                         return txt === 'done' || txt === 'close';
                       });
    if (dismissBtn) {
      COS.Executor.clickEl(dismissBtn);
      await COS.sleep(1500);
    }
    
    // 2. Find the active job card using multiple strategies
    let activeCard = null;
    
    // Strategy 1: Find by active class
    activeCard = document.querySelector('.jobs-search-results-list__list-item--active') || 
                 document.querySelector('[data-job-id].active') ||
                 document.querySelector('.job-card-container--active')?.closest('li');
    
    // Strategy 2: Find by aria-current
    if (!activeCard) {
      activeCard = document.querySelector('[aria-current="true"]')?.closest('li');
    }
    
    // Strategy 3: Find by URL's currentJobId
    if (!activeCard) {
      const urlMatch = window.location.href.match(/currentJobId=(\d+)/);
      if (urlMatch) {
        activeCard = document.querySelector(`[data-job-id="${urlMatch[1]}"]`)?.closest('li');
      }
    }
    
    // Strategy 4: Find by most recent click/focus
    if (!activeCard) {
      const allCards = document.querySelectorAll('.jobs-search-results__list-item');
      activeCard = Array.from(allCards).find(card => 
        card.classList.contains('active') || 
        card.querySelector('.active')
      );
    }
    
    if (!activeCard) {
      Widget.status("Could not find active job card");
      await stop();
      return;
    }
    
    // 3. Find next job card
    let nextCard = activeCard.nextElementSibling;
    while (nextCard && !nextCard.querySelector('[data-job-id], .job-card-list__title')) {
      nextCard = nextCard.nextElementSibling;
    }
    
    const nextLink = nextCard?.querySelector('.job-card-list__title, .job-card-container__link, [data-job-id] a, a');
    
    if (nextLink) {
      COS.Executor.clickEl(nextLink);
      await COS.sleep(3000); // Wait for the new job to load in the right panel
      
      // Start a fresh session for the new job
      State.session.id = COS.uuid();
      State.session.prevElements = [];
      State.session.lastStageHash = null;
      await State.save();
      
      Widget.status("Starting next application...");
      startLoop();
    } else {
      Widget.status("No more jobs found.");
      await stop();
    }
  }

  function schedule(ms) {
    stopLoop();
    if (State.isRunning() && !paused) loopHandle = setTimeout(tick, ms);
  }

  async function tick() {
    if (!State.isRunning() || paused) return;

    // --- Perceive ---
    const all = Scanner.scan();
    const prev = State.session.prevElements || [];
    const elements = Scanner.diff(all, prev);
    const stageHash = Scanner.stageHash(all);

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
    
    // Update progress indicator
    updateProgress(stageHash);

    // --- Think ---
    let resp;
    try {
      const r = await chrome.runtime.sendMessage({ kind: "STEP", payload });
      if (!r || !r.ok) throw new Error(r?.error || "no response");
      resp = r.data;
      consecutiveErrors = 0; // Reset on success
    } catch (e) {
      consecutiveErrors++;
      const retryDelay = getRetryDelay();
      const errorMsg = String(e).slice(0, 60);
      
      Widget.status(
        `Backend error (${consecutiveErrors}/${MAX_CONSECUTIVE_ERRORS})`, 
        errorMsg
      );
      
      if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
        Widget.status("Too many errors — please check backend and restart");
        await stop();
        return;
      }
      
      return schedule(retryDelay);
    }

    Widget.status(resp.stage || "working", resp.source);

    // --- Act ---
    for (const action of resp.script) {
      const result = await Executor.runAction(action);

      if (result.control === "ask_user") {
        paused = true;
        Widget.requestHandoff(action);
        return; // wait for the user; loop resumes in resolveHandoff()
      }
      if (result.control === "done") {
        if (CFG.BULK_APPLY_ENABLED) {
          Widget.status("✅ Done. Loading next...");
          await moveToNextJob();
        } else {
          Widget.status("✅ Application complete");
          await stop();
        }
        return;
      }
      if (result.control === "abort") {
        Widget.status("Aborted");
        await stop();
        return;
      }
      // Human-like pacing between physical actions.
      await COS.sleep(COS.rand(CFG.MIN_ACTION_DELAY_MS, CFG.MAX_ACTION_DELAY_MS));
    }

    schedule(CFG.SETTLE_MS);
  }

  // Called by the widget when the user answers a handoff.
  async function resolveHandoff(payload, action) {
    if (payload.cancelled) {
      Widget.status("Paused — press Stop or continue manually");
      return; // stay paused; user decides
    }
    // If it was a confirm-to-submit, physically click the stored submit target now.
    if (payload.confirmed_submit && action.target_id) {
      const el = Scanner.resolve(action.target_id);
      if (el) Executor.clickEl(el);
    }
    
    // Phase 6: Attach any manual fields the user interacted with during this pause
    if (Object.keys(manualChanges).length > 0) {
      payload.learned_fields = manualChanges;
      manualChanges = {};
    }
    
    pendingUserInput = payload;
    paused = false;
    Widget.status("Resuming…");
    schedule(CFG.SETTLE_MS);
  }

  // Track manual changes while the agent is paused (for Phase 6 learning)
  document.addEventListener("change", (e) => {
    if (!paused || !e.target || !e.target.getAttribute) return;
    const sig = e.target.getAttribute("data-cos-sig");
    if (sig) {
      manualChanges[sig] = e.target.value || (e.target.checked ? "true" : "false");
    }
  }, true);

  // Boot once the DOM is ready.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
