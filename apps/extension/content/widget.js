// The floating control + status panel. Also renders human-in-the-loop handoffs:
// confirm-to-submit, OTP entry, free-text answers, and "I'm done, resume".
(function () {
  const COS = window.COS;

  let root, statusEl, handoffEl, startBtn;
  let onStart, onStop, onHandoffResolve;

  function mount(handlers) {
    onStart = handlers.onStart;
    onStop = handlers.onStop;
    onHandoffResolve = handlers.onHandoffResolve;

    root = document.createElement("div");
    root.id = "cos-widget";
    root.innerHTML = `
      <div class="cos-head">
        <span class="cos-dot" id="cos-dot"></span>
        <span class="cos-title">Career OS</span>
        <button class="cos-min" id="cos-min" title="minimize">–</button>
      </div>
      <div class="cos-body" id="cos-body">
        <div class="cos-status" id="cos-status">Idle</div>
        <div class="cos-handoff" id="cos-handoff" hidden></div>
        <div class="cos-actions">
          <button class="cos-btn cos-primary" id="cos-start">Apply on this page</button>
          <button class="cos-btn" id="cos-stop" hidden>Stop</button>
        </div>
      </div>`;
    document.documentElement.appendChild(root);

    statusEl = root.querySelector("#cos-status");
    handoffEl = root.querySelector("#cos-handoff");
    startBtn = root.querySelector("#cos-start");

    startBtn.onclick = () => onStart && onStart();
    root.querySelector("#cos-stop").onclick = () => onStop && onStop();
    root.querySelector("#cos-min").onclick = () => {
      const body = root.querySelector("#cos-body");
      body.hidden = !body.hidden;
    };
  }

  function setRunning(running) {
    root.querySelector("#cos-dot").classList.toggle("live", running);
    startBtn.hidden = running;
    root.querySelector("#cos-stop").hidden = !running;
  }

  function status(text, source, confidence) {
    let indicator = '';
    if (confidence !== undefined && confidence !== null) {
      if (confidence >= 0.85) indicator = '🟢 ';
      else if (confidence >= 0.60) indicator = '🟡 ';
      else if (confidence >= 0.40) indicator = '🟠 ';
      else indicator = '🔴 ';
    }
    statusEl.textContent = source 
      ? `${indicator}${text}  ·  ${source}` 
      : text;
  }

  // Show recovery dialog for stale sessions
  function showRecoveryDialog(message, onResume, onCancel) {
    handoffEl.hidden = false;
    handoffEl.innerHTML = `
      <div class="cos-hprompt">⏸ ${escapeHtml(message)}</div>
      <button class="cos-btn cos-primary" id="cos-recovery-resume">Resume</button>
      <button class="cos-btn" id="cos-recovery-cancel">Start Fresh</button>
    `;
    
    handoffEl.querySelector('#cos-recovery-resume').onclick = () => {
      handoffEl.hidden = true;
      handoffEl.innerHTML = "";
      onResume && onResume();
    };
    
    handoffEl.querySelector('#cos-recovery-cancel').onclick = () => {
      handoffEl.hidden = true;
      handoffEl.innerHTML = "";
      onCancel && onCancel();
    };
  }

  // Render a handoff request and resolve with the user's response.
  function requestHandoff(action) {
    handoffEl.hidden = false;
    const kind = action.input_kind || "manual";
    const prompt = action.prompt || "I need your help.";

    let inner = `<div class="cos-hprompt">⏸ ${escapeHtml(prompt)}</div>`;
    if (kind === "confirm") {
      inner += `<button class="cos-btn cos-primary" data-act="confirm">Confirm & submit</button>
                <button class="cos-btn" data-act="cancel">Not yet</button>`;
    } else if (kind === "otp") {
      inner += `<input class="cos-input" id="cos-otp" placeholder="Enter code" />
                <button class="cos-btn cos-primary" data-act="otp">Submit code</button>`;
    } else if (kind === "text") {
      inner += `<input class="cos-input" id="cos-text" placeholder="Your answer" />
                <button class="cos-btn cos-primary" data-act="text">Save & continue</button>`;
    } else {
      // manual / file: user acts in the page, then resumes.
      inner += `<button class="cos-btn cos-primary" data-act="resume">I've done it — Resume</button>`;
    }
    handoffEl.innerHTML = inner;

    handoffEl.querySelectorAll("button").forEach((b) => {
      b.onclick = () => {
        const act = b.getAttribute("data-act");
        let payload = { resumed: true };
        if (act === "confirm") payload.confirmed_submit = true;
        if (act === "cancel") payload.cancelled = true;
        if (act === "otp") payload.otp = handoffEl.querySelector("#cos-otp")?.value || "";
        if (act === "text") {
          payload.answer = handoffEl.querySelector("#cos-text")?.value || "";
          payload.question = prompt.replace(/^Please answer:\s*/i, "");
        }
        handoffEl.hidden = true;
        handoffEl.innerHTML = "";
        onHandoffResolve && onHandoffResolve(payload, action);
      };
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  COS.Widget = { mount, setRunning, status, requestHandoff, showRecoveryDialog };
})();
