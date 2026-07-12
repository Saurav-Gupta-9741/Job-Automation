// Act: turn planner JSON actions into native DOM interactions using real event dispatch
// so framework listeners (React/Angular/Vue) actually register the input. Re-locates
// targets by stable signature; verifies values stuck.
(function () {
  const COS = window.COS;
  const Scanner = COS.Scanner;

  // Enhanced retry configuration for stale elements
  const RETRY_CONFIG = {
    MAX_ATTEMPTS: 3,
    RETRY_DELAY_MS: 500,
    STALE_ERRORS: ['stale element', 'not attached', 'detached', 'cannot read properties']
  };

  function isStaleError(error) {
    const msg = String(error).toLowerCase();
    return RETRY_CONFIG.STALE_ERRORS.some(e => msg.includes(e));
  }

  function ensureElementReady(el) {
    if (!el || !el.isConnected) return false;
    if (el.offsetParent === null && el.tagName !== 'BODY') return false; // hidden
    return true;
  }

  function fireInput(el, value) {
    // Use the native value setter so React's tracked value updates.
    const proto = el instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
    if (setter) setter.call(el, value);
    else el.value = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function typeInto(el, value) {
    el.focus();
    if (el.tagName === "SELECT") return selectOption(el, value);
    fireInput(el, value);
    // A trailing keyup helps some autocomplete widgets commit.
    el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, key: "Unidentified" }));
    // Verify it stuck; return success flag.
    return String(el.value).trim() !== "" || el.tagName === "SELECT";
  }

  function selectOption(sel, value) {
    const v = value.toLowerCase().trim();
    let matched = false;
    Array.from(sel.options).forEach((o) => {
      if (!matched && (o.text.toLowerCase().trim() === v ||
                       o.value.toLowerCase().trim() === v ||
                       o.text.toLowerCase().includes(v))) {
        sel.value = o.value;
        matched = true;
      }
    });
    sel.dispatchEvent(new Event("input", { bubbles: true }));
    sel.dispatchEvent(new Event("change", { bubbles: true }));
    return matched;
  }

  function clickEl(el) {
    el.scrollIntoView({ block: "center", behavior: "instant" });
    // Full realistic sequence for stubborn handlers.
    for (const type of ["pointerdown", "mousedown", "pointerup", "mouseup", "click"]) {
      el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    }
    return true;
  }

  async function runAction(action) {
    const el = action.target_id ? Scanner.resolve(action.target_id) : null;

    // DRY RUN MODE: Log actions without executing
    if (COS.CONFIG.DRY_RUN_MODE) {
      console.log('[DRY RUN] Action:', action.type, 'Target:', action.target_id, 'Value:', action.value);
      await COS.sleep(300); // Brief delay to simulate execution
      return { ok: true, dryRun: true };
    }

    // Enhanced action executor with retry logic for stale elements
    for (let attempt = 0; attempt < RETRY_CONFIG.MAX_ATTEMPTS; attempt++) {
      try {
        const result = await _executeAction(action, el, attempt);
        if (result.ok || !result.retry) {
          return result;
        }
        
        // Retry logic: re-resolve element and try again
        if (attempt < RETRY_CONFIG.MAX_ATTEMPTS - 1) {
          await COS.sleep(RETRY_CONFIG.RETRY_DELAY_MS);
          const freshEl = action.target_id ? Scanner.resolve(action.target_id) : null;
          if (freshEl && freshEl !== el) {
            return await _executeAction(action, freshEl, attempt + 1);
          }
        }
      } catch (error) {
        if (isStaleError(error) && attempt < RETRY_CONFIG.MAX_ATTEMPTS - 1) {
          await COS.sleep(RETRY_CONFIG.RETRY_DELAY_MS);
          continue;
        }
        return { ok: false, reason: String(error).slice(0, 100) };
      }
    }
    return { ok: false, reason: "max retries exceeded" };
  }

  async function _executeAction(action, el, attempt) {
    switch (action.type) {
      case "click": {
        if (!el || !ensureElementReady(el)) {
          return { ok: false, retry: true, reason: "target not ready" };
        }
        clickEl(el);
        return { ok: true };
      }
      case "type": {
        if (!el || !ensureElementReady(el)) {
          return { ok: false, retry: true, reason: "target not ready" };
        }
        const ok = typeInto(el, action.value || "");
        return { ok, retry: !ok };
      }
      case "select": {
        if (!el || !ensureElementReady(el)) {
          return { ok: false, retry: true, reason: "target not ready" };
        }
        return { ok: selectOption(el, action.value || "") };
      }
      case "fill_all": {
        let allOk = true;
        for (const f of action.fields || []) {
          const target = Scanner.resolve(f.target_id);
          if (!target || !ensureElementReady(target)) { 
            allOk = false; 
            continue; 
          }
          const ok = f.select
            ? selectOption(target, f.value || "")
            : typeInto(target, f.value || "");
          allOk = allOk && ok;
          await COS.sleep(COS.rand(120, 300)); // human-like inter-field pacing
        }
        return { ok: allOk, retry: !allOk };
      }
      case "upload_resume": {
        try {
          await COS.Upload.uploadResume(el);
          return { ok: true };
        } catch (e) {
          return { ok: false, reason: String(e) };
        }
      }
      case "scroll_down": {
        window.scrollBy({ top: window.innerHeight * 0.8, behavior: "smooth" });
        return { ok: true };
      }
      case "wait": {
        await COS.sleep(action.ms || 1000);
        return { ok: true };
      }
      case "ask_user":
      case "done":
      case "abort":
        return { ok: true, control: action.type };
      default:
        return { ok: false, reason: "unknown action " + action.type };
    }
  }

  COS.Executor = { runAction, clickEl };
})();
