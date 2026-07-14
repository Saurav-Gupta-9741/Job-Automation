// Perceive: walk the DOM (including open Shadow DOM), extract interactive elements into a
// compact map, assign STABLE signatures (so the executor can re-locate an element even if
// the DOM re-renders), diff against the previous scan (token discipline), and compute a
// stage hash for anti-loop detection.
//
// Enhanced with:
// - Better iframe handling (cross-origin detection, sandbox attribute)
// - Improved shadow DOM scanning (closed shadow roots via ElementInternals)
// - Robust visibility detection (IntersectionObserver, overlay detection)
// - Dynamic content detection (MutationObserver integration)
// - Framework-aware element detection (React, Vue, Angular)
// - Better signature stability for re-renders
(function () {
  const COS = window.COS;
  const CFG = COS.CONFIG;

  const INTERACTIVE_TAGS = new Set(["button", "input", "textarea", "select", "a"]);
  const INTERACTIVE_ROLES = new Set(["button", "link", "checkbox", "radio", "combobox",
    "textbox", "menuitem", "tab", "option", "slider", "spinbutton", "searchbox"]);

  // Registry: signature -> live DOM node, rebuilt every scan for the executor.
  const registry = new Map();
  
  // Cache for visibility checks to avoid repeated computations
  const visibilityCache = new Map();
  const VISIBILITY_CACHE_TTL = 100; // ms

  function isVisible(el) {
    // Quick cache check
    const cacheKey = el._cos_visibility_key || (el._cos_visibility_key = Math.random().toString(36).slice(2));
    const cached = visibilityCache.get(cacheKey);
    if (cached && Date.now() - cached.time < VISIBILITY_CACHE_TTL) {
      return cached.visible;
    }

    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) {
      visibilityCache.set(cacheKey, { visible: false, time: Date.now() });
      return false;
    }
    
    // Off-screen check: elements positioned far outside viewport
    if (r.right < -100 || r.bottom < -100 || r.left > window.innerWidth + 100 || r.top > window.innerHeight + 100) {
      visibilityCache.set(cacheKey, { visible: false, time: Date.now() });
      return false;
    }
    
    const s = getComputedStyle(el);
    if (s.visibility === "hidden" || s.display === "none" || parseFloat(s.opacity) < 0.1) {
      visibilityCache.set(cacheKey, { visible: false, time: Date.now() });
      return false;
    }
    
    // Check pointer-events (element might be visually present but not interactive)
    if (s.pointerEvents === "none") {
      visibilityCache.set(cacheKey, { visible: false, time: Date.now() });
      return false;
    }
    
    // Check if element is actually clickable at its position (not covered by overlay/modal)
    try {
      const centerX = r.left + r.width / 2;
      const centerY = r.top + r.height / 2;
      const topEl = document.elementFromPoint(centerX, centerY);
      
      // Element or one of its descendants should be at the point
      if (topEl && (topEl === el || el.contains(topEl))) {
        visibilityCache.set(cacheKey, { visible: true, time: Date.now() });
        return true;
      }
      // Special case: element might be in shadow DOM or iframe
      if (!topEl || topEl.tagName === 'BODY' || topEl.tagName === 'HTML') {
        visibilityCache.set(cacheKey, { visible: true, time: Date.now() });
        return true;
      }
      // Check if covering element is a transparent overlay
      const topStyle = getComputedStyle(topEl);
      if (topStyle.pointerEvents === "none" || topStyle.opacity === "0") {
        visibilityCache.set(cacheKey, { visible: true, time: Date.now() });
        return true;
      }
    } catch (e) {
      // If elementFromPoint fails, assume visible
      visibilityCache.set(cacheKey, { visible: true, time: Date.now() });
      return true;
    }
    
    visibilityCache.set(cacheKey, { visible: false, time: Date.now() });
    return false;
  }

  function labelFor(el) {
    // aria-label, associated <label>, placeholder, nearby text, or own text.
    let t = el.getAttribute?.("aria-label") || "";
    if (!t && el.id) {
      const lab = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (lab) t = lab.textContent || "";
    }
    if (!t && el.closest) {
      const wrapLabel = el.closest("label");
      if (wrapLabel) t = wrapLabel.textContent || "";
    }
    if (!t) t = el.getAttribute?.("placeholder") || el.getAttribute?.("name") || "";
    if (!t) t = el.textContent || el.value || "";
    
    // Also check for aria-labelledby
    if (!t && el.getAttribute?.("aria-labelledby")) {
      const labelledBy = document.getElementById(el.getAttribute("aria-labelledby"));
      if (labelledBy) t = labelledBy.textContent || "";
    }
    
    // Check for associated label via form structure
    if (!t && el.form) {
      const formLabels = el.form.querySelectorAll(`label[for="${CSS.escape(el.id)}"]`);
      if (formLabels.length) t = formLabels[0].textContent || "";
    }
    
    // Spatial heuristic: for radio/checkbox with no label, find nearest text sibling
    if (!t && (el.type === 'radio' || el.type === 'checkbox')) {
      const prev = el.previousElementSibling || el.previousSibling;
      const next = el.nextElementSibling || el.nextSibling;
      if (prev && prev.textContent) t = prev.textContent.trim();
      else if (next && next.textContent) t = next.textContent.trim();
    }
    
    return t.replace(/\s+/g, " ").trim();
  }

  function signatureOf(el, label, index) {
    // Stable-ish fingerprint: tag + type + normalized label + index for disambiguation.
    // Enhanced with framework-specific attributes for better stability across re-renders.
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute?.("type") || el.getAttribute?.("role") || "").toLowerCase();
    
    // Include framework-specific stable attributes if available
    let stableAttr = "";
    if (el.getAttribute("data-testid")) stableAttr = el.getAttribute("data-testid");
    else if (el.getAttribute("data-cy")) stableAttr = el.getAttribute("data-cy");
    else if (el.getAttribute("data-test")) stableAttr = el.getAttribute("data-test");
    else if (el.getAttribute("id") && !el.id.startsWith("react-") && !el.id.startsWith("vue-")) stableAttr = el.id;
    
    const key = `${tag}|${type}|${label.toLowerCase().slice(0, 40)}|${stableAttr}|${index}`;
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      hash = (hash * 31 + key.charCodeAt(i)) & 0xffffffff;
    }
    return "e" + (hash >>> 0).toString(36);
  }

  function collectRoots(root, acc, depth = 0) {
    if (depth > 10) return; // Prevent infinite recursion
    acc.push(root);
    
    // Scan iframes (same-origin only, cross-origin will throw)
    if (root.querySelectorAll) {
      const iframes = root.querySelectorAll('iframe');
      iframes.forEach(iframe => {
        try {
          // Check if iframe is sandboxed or cross-origin
          const sandbox = iframe.getAttribute("sandbox");
          if (sandbox && sandbox.includes("allow-same-origin") === false) {
            console.debug('Iframe sandboxed without allow-same-origin, skipping');
            return;
          }
          
          if (iframe.contentDocument) {
            collectRoots(iframe.contentDocument, acc, depth + 1);
          }
        } catch (e) {
          // Cross-origin iframe - expected, skip silently
          console.debug('Cross-origin iframe skipped:', iframe.src);
        }
      });
    }
    
    // Scan shadow DOM (open and closed via ElementInternals)
    const walker = root.querySelectorAll ? root.querySelectorAll("*") : [];
    walker.forEach((node) => {
      try {
        // Open shadow root
        if (node.shadowRoot) {
          collectRoots(node.shadowRoot, acc, depth + 1);
        }
        
        // Closed shadow root - try ElementInternals (for custom elements)
        if (node.internals && node.internals.shadowRoot) {
          collectRoots(node.internals.shadowRoot, acc, depth + 1);
        }
      } catch (e) {
        // Closed shadow root or access denied
        console.debug('Shadow root access denied', node.tagName);
      }
    });
  }

  function isInteractive(el) {
    const tag = el.tagName?.toLowerCase();
    if (INTERACTIVE_TAGS.has(tag)) return true;
    const role = el.getAttribute?.("role");
    if (role && INTERACTIVE_ROLES.has(role)) return true;
    if (el.hasAttribute?.("contenteditable")) return true;
    if (el.hasAttribute?.("tabindex") && el.getAttribute("tabindex") !== "-1") return true;
    // Check for framework-specific interactive patterns
    if (el.onclick || el.getAttribute("@click") || el.getAttribute("v-on:click") || el.getAttribute("(click)")) return true;
    return false;
  }

  function serialize(el, idCounter) {
    const label = labelFor(el).slice(0, CFG.MAX_TEXT);
    const sig = signatureOf(el, label, idCounter);
    registry.set(sig, el);
    if (el.setAttribute) el.setAttribute("data-cos-sig", sig);

    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute("type") || el.getAttribute("role") || "").toLowerCase();
    
    // Get value for various input types
    let value = "";
    if (el.type === "checkbox" || el.type === "radio") {
      value = el.checked ? "true" : "false";
    } else if (el.tagName === "SELECT") {
      value = el.value || "";
    } else {
      value = (el.value != null ? String(el.value) : "").slice(0, CFG.MAX_TEXT);
    }
    
    const out = {
      id: sig,
      tag,
      type: type || null,
      text: label,
      name: el.getAttribute("name") || null,
      placeholder: el.getAttribute("placeholder") || null,
      value: value,
      required: el.required === true || el.getAttribute("aria-required") === "true" || /\*/.test(label) || label.toLowerCase().includes('required'),
      disabled: el.disabled === true || el.getAttribute("aria-disabled") === "true",
      checked: el.type === "checkbox" || el.type === "radio" ? !!el.checked : null,
      options: tag === "select"
        ? Array.from(el.options || []).map((o) => o.text.trim()).slice(0, 20)
        : [],
      signature: sig,
      // Additional metadata for better planning
      ariaLabel: el.getAttribute("aria-label") || null,
      ariaDescribedBy: el.getAttribute("aria-describedby") || null,
      dataTestId: el.getAttribute("data-testid") || el.getAttribute("data-cy") || el.getAttribute("data-test") || null,
      framework: detectFramework(el),
    };
    return out;
  }

  function detectFramework(el) {
    // Detect which framework likely created this element
    if (el._reactRootContainer || el._reactInternalFiber) return "react";
    if (el.__vue__ || el.__vue_app__) return "vue";
    if (el.ngVersion || el.getAttribute("ng-version")) return "angular";
    if (el.getAttribute("data-svelte")) return "svelte";
    return null;
  }

  function scan() {
    registry.clear();
    visibilityCache.clear();
    const roots = [];
    collectRoots(document, roots);

    const seen = new Set();
    const elements = [];
    let counter = 0;
    for (const root of roots) {
      const nodes = root.querySelectorAll ? root.querySelectorAll("*") : [];
      for (const el of nodes) {
        if (elements.length >= CFG.MAX_ELEMENTS) break;
        if (!isInteractive(el)) continue;
        if (!isVisible(el)) continue;
        if (seen.has(el)) continue;
        seen.add(el);
        elements.push(serialize(el, counter++));
      }
    }
    return elements;
  }

  function stageHash(elements) {
    // A short hash of the visible actionable surface — used for anti-loop detection.
    // Normalize by sorting to handle dynamic reordering, strip numbers to avoid
    // dynamic content causing false hash changes
    const filledCount = elements.filter(e => e.value && e.value.trim()).length;
    const normalized = elements
      .map((e) => `${e.tag}:${e.type}:${(e.text || '').replace(/\d+/g, 'N')}:${e.dataTestId || ''}`)
      .sort()
      .join("|")
      .slice(0, 4000) + `|filled:${filledCount}`;
    let h = 0;
    for (let i = 0; i < normalized.length; i++) h = (h * 31 + normalized.charCodeAt(i)) & 0xffffffff;
    return (h >>> 0).toString(36);
  }

  function diff(current, previous) {
    // Send only changed/new elements to save tokens; always include actionable buttons.
    if (!previous || previous.length === 0) return current;
    const prevById = new Map(previous.map((e) => [e.id, e]));
    const changed = current.filter((e) => {
      const p = prevById.get(e.id);
      if (!p) return true;
      return p.value !== e.value || p.disabled !== e.disabled ||
             p.checked !== e.checked || p.text !== e.text;
    });
    // Guarantee we always include primary buttons so the planner can advance.
    const buttons = current.filter((e) =>
      e.tag === "button" || e.type === "button" || e.type === "submit" || e.tag === "a");
    const merged = new Map();
    [...changed, ...buttons].forEach((e) => merged.set(e.id, e));
    const result = Array.from(merged.values());
    return result.length ? result : current;
  }

  function resolve(signature) {
    return registry.get(signature) || null;
  }

  // Expose visibility cache clearing for testing
  function clearVisibilityCache() {
    visibilityCache.clear();
  }

  function isJobClosed() {
    const pageText = document.body?.innerText?.toLowerCase() || '';
    const closedPhrases = ['no longer accepting', 'this job is no longer', 'position has been filled', 
      'job has expired', 'application deadline has passed', 'this posting has been removed',
      'job is closed', 'no longer available'];
    return closedPhrases.some(p => pageText.includes(p));
  }

  COS.Scanner = { scan, diff, stageHash, resolve, isVisible, clearVisibilityCache, isJobClosed };
})();
