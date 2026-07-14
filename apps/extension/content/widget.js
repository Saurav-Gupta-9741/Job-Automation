// Career OS Widget — Premium draggable panel with BYOK setup flow
(function () {
  const COS = window.COS;
  let root, statusEl, statusMini, handoffEl, startBtn, quotaFill, settingsPanel, tierBadge;
  let onStart, onStop, onHandoffResolve;
  let settingsOpen = false;

  // Drag state
  let isDragging = false, dragOffsetX = 0, dragOffsetY = 0;

  function mount(handlers) {
    onStart = handlers.onStart;
    onStop = handlers.onStop;
    onHandoffResolve = handlers.onHandoffResolve;

    root = document.createElement("div");
    root.id = "cos-widget";
    root.classList.add("collapsed");
    root.innerHTML = `
      <div class="cos-head" id="cos-head">
        <div class="cos-logo">C</div>
        <span class="cos-dot" id="cos-dot"></span>
        <span class="cos-title">Career OS</span>
        <span class="cos-tier cos-tier-free" id="cos-tier">FREE</span>
        <span class="cos-status-mini" id="cos-status-mini">Ready</span>
        <div class="cos-head-btns">
          <button class="cos-settings-btn" id="cos-settings-btn" title="Settings">⚙</button>
          <button class="cos-min" id="cos-min" title="Collapse">−</button>
        </div>
      </div>
      <div class="cos-body" id="cos-body">
        <div class="cos-status" id="cos-status">Ready — open a job listing and click Apply</div>
        <div class="cos-quota-bar"><div class="cos-quota-fill" id="cos-quota-fill" style="width:0%"></div></div>
        <div class="cos-handoff" id="cos-handoff" hidden></div>
        <div class="cos-actions">
          <button class="cos-btn cos-primary" id="cos-start">⚡ Apply to This Job</button>
          <button class="cos-btn" id="cos-stop" hidden>■ Stop</button>
        </div>
      </div>
      <div class="cos-settings" id="cos-settings" hidden>
        <div class="cos-settings-title">⚙ Settings — Bring Your Own Key</div>
        <div class="cos-field-label">LLM Provider</div>
        <select class="cos-select" id="cos-provider">
          <option value="groq">Groq (free tier available)</option>
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic (Claude)</option>
          <option value="google">Google (Gemini)</option>
          <option value="together">Together AI</option>
          <option value="openrouter">OpenRouter</option>
        </select>
        <div class="cos-field-label">Your API Key</div>
        <input class="cos-input" id="cos-api-key" type="password" placeholder="sk-... or gsk_..." />
        <div class="cos-field-label">Model (optional override)</div>
        <input class="cos-input" id="cos-model" placeholder="e.g. gpt-4o-mini, claude-sonnet-4" />
        <button class="cos-save-btn" id="cos-save-settings">Save Settings</button>
      </div>`;
    document.documentElement.appendChild(root);

    statusEl = root.querySelector("#cos-status");
    statusMini = root.querySelector("#cos-status-mini");
    handoffEl = root.querySelector("#cos-handoff");
    startBtn = root.querySelector("#cos-start");
    quotaFill = root.querySelector("#cos-quota-fill");
    settingsPanel = root.querySelector("#cos-settings");
    tierBadge = root.querySelector("#cos-tier");

    startBtn.onclick = () => onStart && onStart();
    root.querySelector("#cos-stop").onclick = () => onStop && onStop();

    root.querySelector("#cos-head").addEventListener("click", (e) => {
      if (isDragging) return;
      if (e.target.closest(".cos-head-btns")) return;
      root.classList.toggle("collapsed");
      if (!root.classList.contains("collapsed")) loadSettings();
    });

    root.querySelector("#cos-min").onclick = (e) => {
      e.stopPropagation();
      root.classList.add("collapsed");
      settingsPanel.hidden = true;
      settingsOpen = false;
    };

    root.querySelector("#cos-settings-btn").onclick = (e) => {
      e.stopPropagation();
      settingsOpen = !settingsOpen;
      settingsPanel.hidden = !settingsOpen;
      if (settingsOpen) loadSettings();
    };

    root.querySelector("#cos-save-settings").onclick = saveSettings;

    initDrag();

    // Restore saved position
    const saved = localStorage.getItem("cos-widget-pos");
    if (saved) {
      try {
        const { x, y } = JSON.parse(saved);
        root.style.right = "auto";
        root.style.bottom = "auto";
        root.style.left = Math.min(x, window.innerWidth - 50) + "px";
        root.style.top = Math.min(y, window.innerHeight - 50) + "px";
      } catch (_) {}
    }

    // Check if API key is configured — if not, prompt setup
    checkFirstLaunch();
  }

  // ── First launch: check if API key is set ──
  async function checkFirstLaunch() {
    try {
      const r = await chrome.runtime.sendMessage({ kind: "GET_CONFIG" });
      if (r && r.ok && !r.data.has_key) {
        // No API key — show setup prompt
        root.classList.remove("collapsed");
        settingsOpen = true;
        settingsPanel.hidden = false;
        status("⚠ Setup required — add your API key in Settings below");
        statusMini.textContent = "Setup";
      }
    } catch (_) {
      // Backend not running — show connection help
      status("⚠ Backend not running — start the server first");
      statusMini.textContent = "Offline";
    }
  }

  // ── Drag logic ──
  function initDrag() {
    const head = root.querySelector("#cos-head");
    let startX, startY;

    head.addEventListener("pointerdown", (e) => {
      if (e.target.closest("button") || e.target.closest("input")) return;
      startX = e.clientX;
      startY = e.clientY;
      const rect = root.getBoundingClientRect();
      dragOffsetX = e.clientX - rect.left;
      dragOffsetY = e.clientY - rect.top;
      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onUp);
    });

    function onMove(e) {
      if (Math.abs(e.clientX - startX) > 4 || Math.abs(e.clientY - startY) > 4) {
        isDragging = true;
        root.classList.add("dragging");
      }
      if (!isDragging) return;
      e.preventDefault();
      e.stopPropagation();
      let x = e.clientX - dragOffsetX;
      let y = e.clientY - dragOffsetY;
      x = Math.max(0, Math.min(window.innerWidth - root.offsetWidth, x));
      y = Math.max(0, Math.min(window.innerHeight - root.offsetHeight, y));
      root.style.right = "auto";
      root.style.bottom = "auto";
      root.style.left = x + "px";
      root.style.top = y + "px";
    }

    function onUp(e) {
      e.stopPropagation();
      e.preventDefault();
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
      root.classList.remove("dragging");
      if (isDragging) {
        localStorage.setItem("cos-widget-pos", JSON.stringify({
          x: parseInt(root.style.left), y: parseInt(root.style.top),
        }));
      }
      setTimeout(() => { isDragging = false; }, 50);
    }
  }

  // ── Settings: load/save ──
  async function loadSettings() {
    try {
      const data = await chrome.storage.sync.get(["cos_provider", "cos_api_key", "cos_model"]);
      if (data.cos_provider) root.querySelector("#cos-provider").value = data.cos_provider;
      if (data.cos_api_key) root.querySelector("#cos-api-key").value = data.cos_api_key;
      if (data.cos_model) root.querySelector("#cos-model").value = data.cos_model;
    } catch (_) {}
  }

  async function saveSettings() {
    const provider = root.querySelector("#cos-provider").value;
    const apiKey = root.querySelector("#cos-api-key").value.trim();
    const model = root.querySelector("#cos-model").value.trim();
    const btn = root.querySelector("#cos-save-settings");

    if (!apiKey) {
      btn.textContent = "⚠ API Key required!";
      btn.style.background = "linear-gradient(135deg, #ef4444, #dc2626)";
      setTimeout(() => {
        btn.textContent = "Save Settings";
        btn.style.background = "";
      }, 2000);
      return;
    }

    try {
      await chrome.storage.sync.set({ cos_provider: provider, cos_api_key: apiKey, cos_model: model });
      await chrome.runtime.sendMessage({
        kind: "SAVE_CONFIG", config: { provider, api_key: apiKey, model }
      });
      btn.textContent = "✓ Saved!";
      btn.style.background = "linear-gradient(135deg, #10b981, #059669)";
      status("Ready — open a job listing and click Apply");
      statusMini.textContent = "Ready";
      setTimeout(() => {
        btn.textContent = "Save Settings";
        btn.style.background = "";
      }, 2000);
    } catch (e) {
      btn.textContent = "Error — check backend";
      setTimeout(() => { btn.textContent = "Save Settings"; btn.style.background = ""; }, 2000);
    }
  }

  // ── Public API ──

  function setRunning(running) {
    root.querySelector("#cos-dot").classList.toggle("live", running);
    startBtn.hidden = running;
    root.querySelector("#cos-stop").hidden = !running;
    if (running) root.classList.remove("collapsed");
  }

  function status(text, source) {
    const display = source ? `${text} · ${source}` : text;
    statusEl.textContent = display;
    statusMini.textContent = text.slice(0, 18) || "Ready";
  }

  function showQuotaInfo(used, limit, tier) {
    const pct = Math.min((used / limit) * 100, 100);
    quotaFill.style.width = pct + "%";
    quotaFill.classList.toggle("warn", pct >= 80);
    tierBadge.textContent = tier === "pro" ? "PRO" : "FREE";
    tierBadge.className = `cos-tier cos-tier-${tier === "pro" ? "pro" : "free"}`;
    status(`${tier === "pro" ? "Pro" : "Free"}: ${used}/${limit} applied this month`);
  }

  function showRecoveryDialog(message, onResume, onCancel) {
    root.classList.remove("collapsed");
    handoffEl.hidden = false;
    handoffEl.innerHTML = `
      <div class="cos-hprompt">⏸ ${esc(message)}</div>
      <div class="cos-actions">
        <button class="cos-btn cos-primary" id="cos-rr">Resume</button>
        <button class="cos-btn" id="cos-rc">Start Fresh</button>
      </div>`;
    handoffEl.querySelector("#cos-rr").onclick = () => { handoffEl.hidden = true; onResume && onResume(); };
    handoffEl.querySelector("#cos-rc").onclick = () => { handoffEl.hidden = true; onCancel && onCancel(); };
  }

  function showUpgradePrompt(message) {
    root.classList.remove("collapsed");
    setRunning(false);
    handoffEl.hidden = false;
    handoffEl.innerHTML = `
      <div class="cos-upgrade">
        <div class="cos-upgrade-title">⚡ Upgrade to Pro</div>
        <div class="cos-upgrade-desc">${esc(message)}</div>
        <button class="cos-buy-btn" id="cos-buy-pro">Get Pro — ₹11/month</button>
        <div class="cos-divider">— or enter license key —</div>
        <input class="cos-input" id="cos-license-key" placeholder="COS-XXXX-XXXX" />
        <button class="cos-btn cos-primary" id="cos-activate-key" style="margin-top:6px;width:100%">Activate Key</button>
      </div>`;
    handoffEl.querySelector("#cos-buy-pro").onclick = () => {
      window.open("https://career-os.dev/pricing", "_blank");
    };
    handoffEl.querySelector("#cos-activate-key").onclick = async () => {
      const key = handoffEl.querySelector("#cos-license-key").value.trim();
      if (!key) return;
      const btn = handoffEl.querySelector("#cos-activate-key");
      btn.textContent = "Activating…"; btn.disabled = true;
      try {
        const r = await chrome.runtime.sendMessage({ kind: "ACTIVATE_LICENSE", key });
        if (r && r.ok) {
          handoffEl.innerHTML = `<div class="cos-upgrade">
            <div class="cos-upgrade-title" style="-webkit-text-fill-color:#10b981">✅ Pro Activated!</div>
            <div class="cos-upgrade-desc">50 applications/month unlocked.</div></div>`;
          tierBadge.textContent = "PRO";
          tierBadge.className = "cos-tier cos-tier-pro";
          setTimeout(() => { handoffEl.hidden = true; }, 3000);
        } else { btn.textContent = "Invalid Key"; btn.disabled = false; }
      } catch (_) { btn.textContent = "Error"; btn.disabled = false; }
    };
  }

  function requestHandoff(action) {
    root.classList.remove("collapsed");
    handoffEl.hidden = false;
    const kind = action.input_kind || "manual";
    const prompt = action.prompt || "I need your help.";

    let inner = `<div class="cos-hprompt">⏸ ${esc(prompt)}</div>`;
    if (kind === "confirm") {
      inner += `<div class="cos-actions"><button class="cos-btn cos-primary" data-act="confirm">Confirm & Submit</button>
                <button class="cos-btn" data-act="cancel">Not yet</button></div>`;
    } else if (kind === "otp") {
      inner += `<input class="cos-input" id="cos-otp" placeholder="Enter code" />
                <button class="cos-btn cos-primary" data-act="otp" style="width:100%">Submit Code</button>`;
    } else if (kind === "text") {
      inner += `<input class="cos-input" id="cos-text" placeholder="Your answer" />
                <button class="cos-btn cos-primary" data-act="text" style="width:100%">Save & Continue</button>`;
    } else {
      inner += `<button class="cos-btn cos-primary" data-act="resume" style="width:100%">Done — Resume Agent</button>`;
    }
    handoffEl.innerHTML = inner;

    handoffEl.querySelectorAll("[data-act]").forEach((b) => {
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
        onHandoffResolve && onHandoffResolve(payload, action);
      };
    });
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, c =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  COS.Widget = { mount, setRunning, status, showQuotaInfo,
                  requestHandoff, showRecoveryDialog, showUpgradePrompt };
})();
