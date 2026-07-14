// Act: turn planner JSON actions into native DOM interactions using real event dispatch
// so framework listeners (React/Angular/Vue/Svelte) actually register the input. Re-locates
// targets by stable signature; verifies values stuck.
//
// Enhanced with:
// - Framework-aware event dispatching (React, Vue, Angular, Svelte)
// - Better stale element recovery with re-scanning
// - Improved visibility and readiness checks
// - Support for complex input types (date, file, color, etc.)
// - Better error handling and logging
// - Human-like interaction patterns
(function () {
  const COS = window.COS;
  const Scanner = COS.Scanner;

  // Enhanced retry configuration for stale elements
  const RETRY_CONFIG = {
    MAX_ATTEMPTS: 5,
    RETRY_DELAY_MS: 500,
    STALE_ERRORS: [
      'stale element', 'not attached', 'detached', 'cannot read properties',
      'element not found', 'no such element', 'element is not attached',
      'node is not attached', 'disconnected', 'removed from dom'
    ]
  };

  function isStaleError(error) {
    const msg = String(error).toLowerCase();
    return RETRY_CONFIG.STALE_ERRORS.some(e => msg.includes(e));
  }

  function ensureElementReady(el) {
    if (!el || !el.isConnected) return false;
    if (el.offsetParent === null && el.tagName !== 'BODY') return false; // hidden
    // Check if element is actually interactable
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') return false;
    if (style.pointerEvents === 'none') return false;
    return true;
  }

  function getFramework(el) {
    // Detect which framework manages this element
    if (el._reactRootContainer || el._reactInternalFiber || el.__reactFiber) return 'react';
    if (el.__vue__ || el.__vue_app__ || el.__vueParentComponent) return 'vue';
    if (el.ngVersion || el.getAttribute('ng-version') || el._ngContext) return 'angular';
    if (el.getAttribute('data-svelte') || el.__svelte_meta) return 'svelte';
    return null;
  }

  function dispatchFrameworkEvents(el, eventType, options = {}) {
    // Dispatch events in a way that works with all major frameworks.
    const framework = getFramework(el);
    const baseOptions = { bubbles: true, cancelable: true, composed: true, ...options };
    
    // Standard event
    const event = new Event(eventType, baseOptions);
    el.dispatchEvent(event);
    
    // Framework-specific events
    if (framework === 'react') {
      // React needs native events for onChange/onInput
      if (eventType === 'input' || eventType === 'change') {
        const nativeEvent = new Event(eventType, { bubbles: true, cancelable: true });
        // React 17+ uses different internal properties
        Object.defineProperty(nativeEvent, 'target', { value: el, enumerable: true });
        el.dispatchEvent(nativeEvent);
      }
    } else if (framework === 'vue') {
      // Vue listens to native events but may need additional triggers
      if (eventType === 'input') {
        el.dispatchEvent(new Event('input', baseOptions));
      }
    } else if (framework === 'angular') {
      // Angular uses (input) and (change) bindings
      if (eventType === 'input') {
        el.dispatchEvent(new Event('input', baseOptions));
      }
    }
    
    return event;
  }

  function fireInput(el, value) {
    // Use the native value setter so React's tracked value updates.
    const proto = el instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
    if (setter) setter.call(el, value);
    else el.value = value;
    
    // Dispatch framework-aware events
    dispatchFrameworkEvents(el, 'input');
    dispatchFrameworkEvents(el, 'change');
    
    // Also trigger blur/focus for validation
    el.dispatchEvent(new FocusEvent('blur', { bubbles: true }));
    el.dispatchEvent(new FocusEvent('focus', { bubbles: true }));
    
    // Full validation event suite for Angular/Lever
    el.dispatchEvent(new FocusEvent('focusout', { bubbles: true }));
    const lastChar = String(value).slice(-1) || 'a';
    el.dispatchEvent(new KeyboardEvent('keydown', { key: lastChar, bubbles: true, composed: true }));
    el.dispatchEvent(new KeyboardEvent('keyup', { key: lastChar, bubbles: true, composed: true }));
  }

  function typeInto(el, value) {
    el.focus();
    if (el.tagName === "SELECT") return selectOption(el, value);
    
    // ContentEditable support
    if (el.getAttribute('contenteditable') === 'true' || el.isContentEditable) {
      el.focus();
      el.innerHTML = value;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }
    
    // Handle different input types
    if (el.type === 'date' || el.type === 'datetime-local' || el.type === 'time') {
      let normalized = value;
      // Try to parse common date formats into YYYY-MM-DD
      if (el.type === 'date' && !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        const parsed = new Date(value);
        if (!isNaN(parsed.getTime())) {
          normalized = parsed.toISOString().split('T')[0];
        }
      }
      el.value = normalized;
      dispatchFrameworkEvents(el, 'input');
      dispatchFrameworkEvents(el, 'change');
      return true;
    }
    
    if (el.type === 'file') {
      // File inputs can't be set programmatically for security
      return false;
    }
    
    if (el.type === 'checkbox' || el.type === 'radio') {
      const v = String(value).toLowerCase().trim();
      const elValue = (el.value || '').toLowerCase().trim();
      const elLabel = (el.getAttribute('aria-label') || el.closest('label')?.textContent || '').toLowerCase().trim();
      el.checked = v === 'true' || v === 'yes' || v === '1' || v === elValue || elLabel.includes(v) || v.includes(elLabel);
      dispatchFrameworkEvents(el, 'change');
      return el.checked;
    }
    
    // Phone number formatting: type character by character so input masks can format
    if (el.type === 'tel') {
      el.focus();
      const digits = value.replace(/[^\d+]/g, '');
      for (const ch of digits) {
        el.dispatchEvent(new KeyboardEvent('keydown', { key: ch, bubbles: true }));
        fireInput(el, el.value + ch);
        el.dispatchEvent(new KeyboardEvent('keyup', { key: ch, bubbles: true }));
      }
      return String(el.value).trim() !== '';
    }
    
    // Number field: strip non-numeric characters
    if (el.type === 'number') {
      value = value.replace(/[^\d.\-]/g, '');
    }
    
    fireInput(el, value);
    // A trailing keyup helps some autocomplete widgets commit.
    el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, key: "Unidentified", composed: true }));
    // Verify it stuck; return success flag.
    return String(el.value).trim() !== "" || el.tagName === "SELECT";
  }

  function selectOption(sel, value) {
    const v = value.toLowerCase().trim();
    let matched = false;
    let matchedOption = null;
    
    Array.from(sel.options).forEach((o) => {
      if (!matched && (o.text.toLowerCase().trim() === v ||
                       o.value.toLowerCase().trim() === v ||
                       o.text.toLowerCase().includes(v) ||
                       o.value.toLowerCase().includes(v))) {
        sel.value = o.value;
        matched = true;
        matchedOption = o;
      }
    });
    
    // Second-pass fuzzy matcher: word overlap
    if (!matched) {
      const vWords = v.split(/\s+/).filter(Boolean);
      let bestOverlap = 0;
      let bestOption = null;
      Array.from(sel.options).forEach((o) => {
        const oWords = o.text.toLowerCase().trim().split(/\s+/).filter(Boolean);
        const overlap = vWords.filter(w => oWords.includes(w)).length;
        const threshold = Math.ceil(vWords.length * 0.5);
        if (overlap >= threshold && overlap > bestOverlap) {
          bestOverlap = overlap;
          bestOption = o;
        }
      });
      if (bestOption) {
        sel.value = bestOption.value;
        matched = true;
        matchedOption = bestOption;
      }
    }
    
    if (matched) {
      dispatchFrameworkEvents(sel, 'input');
      dispatchFrameworkEvents(sel, 'change');
      // Also trigger blur for validation
      sel.dispatchEvent(new FocusEvent('blur', { bubbles: true }));
    }
    return matched;
  }

  async function clickEl(el) {
    el.scrollIntoView({ block: "center", behavior: "instant" });
    
    // Wait a tiny bit for scroll to complete
    // Full realistic sequence for stubborn handlers.
    const eventTypes = ["pointerdown", "mousedown", "pointerup", "mouseup", "click"];
    for (const type of eventTypes) {
      const event = new MouseEvent(type, { 
        bubbles: true, 
        cancelable: true, 
        view: window,
        composed: true,
        clientX: el.getBoundingClientRect().left + el.offsetWidth / 2,
        clientY: el.getBoundingClientRect().top + el.offsetHeight / 2,
      });
      el.dispatchEvent(event);
      // Small random delay between events to avoid bot-like jitter
      await COS.sleep(COS.rand(20, 80));
    }
    
    // For React, also dispatch on the document for event delegation
    if (getFramework(el) === 'react') {
      for (const type of eventTypes) {
        const event = new MouseEvent(type, { 
          bubbles: true, 
          cancelable: true, 
          view: window,
          composed: true,
        });
        document.dispatchEvent(event);
        await COS.sleep(COS.rand(20, 80));
      }
    }
    
    return true;
  }

  async function selectCustomDropdown(el, value) {
    // Handle custom combobox/listbox ARIA dropdown widgets
    await clickEl(el); // Open the dropdown menu
    await COS.sleep(500); // Wait for menu to render
    
    const options = document.querySelectorAll('[role="option"]');
    const v = value.toLowerCase().trim();
    const vWords = v.split(/\s+/).filter(Boolean);
    
    let bestMatch = null;
    let bestScore = 0;
    
    for (const opt of options) {
      const optText = (opt.textContent || '').toLowerCase().trim();
      // Exact or includes match
      if (optText === v || optText.includes(v) || v.includes(optText)) {
        bestMatch = opt;
        bestScore = Infinity;
        break;
      }
      // Fuzzy word overlap
      const oWords = optText.split(/\s+/).filter(Boolean);
      const overlap = vWords.filter(w => oWords.includes(w)).length;
      if (overlap > bestScore) {
        bestScore = overlap;
        bestMatch = opt;
      }
    }
    
    if (bestMatch) {
      await clickEl(bestMatch);
      return true;
    }
    return false;
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
        const currentEl = action.target_id ? Scanner.resolve(action.target_id) : null;
        const result = await _executeAction(action, currentEl, attempt);
        if (result.ok || !result.retry) {
          return result;
        }
        
        // Retry logic: wait and try again (element will be re-resolved in next iteration)
        if (attempt < RETRY_CONFIG.MAX_ATTEMPTS - 1) {
          await COS.sleep(RETRY_CONFIG.RETRY_DELAY_MS * (attempt + 1)); // Exponential backoff
          continue;
        }
      } catch (error) {
        if (isStaleError(error) && attempt < RETRY_CONFIG.MAX_ATTEMPTS - 1) {
          await COS.sleep(RETRY_CONFIG.RETRY_DELAY_MS * (attempt + 1));
          continue;
        }
        console.error('Executor error:', error);
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
        await clickEl(el);
        // Wait a bit for any navigation or modal to appear
        await COS.sleep(300);
        return { ok: true };
      }
      case "type": {
        if (!el || !ensureElementReady(el)) {
          return { ok: false, retry: true, reason: "target not ready" };
        }
        // Custom combobox/listbox handling
        if (el.getAttribute('role') === 'combobox' || el.getAttribute('role') === 'listbox') {
          const ok = await selectCustomDropdown(el, action.value || "");
          return { ok, retry: !ok };
        }
        const ok = typeInto(el, action.value || "");
        return { ok, retry: !ok };
      }
      case "select": {
        if (!el || !ensureElementReady(el)) {
          return { ok: false, retry: true, reason: "target not ready" };
        }
        // Custom combobox/listbox handling
        if (el.getAttribute('role') === 'combobox' || el.getAttribute('role') === 'listbox') {
          const ok = await selectCustomDropdown(el, action.value || "");
          return { ok, retry: !ok };
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
          await COS.sleep(COS.rand(150, 400)); // human-like inter-field pacing
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
        await COS.sleep(500); // Wait for lazy-loaded content
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
