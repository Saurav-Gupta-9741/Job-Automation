// Perceive: walk the DOM (including open Shadow DOM), extract interactive elements into a
// compact map, assign STABLE signatures (so the executor can re-locate an element even if
// the DOM re-renders), diff against the previous scan (token discipline), and compute a
// stage hash for anti-loop detection.
(function () {
  const COS = window.COS;
  const CFG = COS.CONFIG;

  const INTERACTIVE_TAGS = new Set(["button", "input", "textarea", "select", "a"]);
  const INTERACTIVE_ROLES = new Set(["button", "link", "checkbox", "radio", "combobox",
    "textbox", "menuitem", "tab", "option"]);

  // Registry: signature -> live DOM node, rebuilt every scan for the executor.
  const registry = new Map();

  function isVisible(el) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return false;
    
    const s = getComputedStyle(el);
    if (s.visibility === "hidden" || s.display === "none" || s.opacity === "0") {
      return false;
    }
    
    // Check pointer-events (element might be visually present but not interactive)
    if (s.pointerEvents === "none") return false;
    
    // Check if element is actually clickable at its position (not covered by overlay/modal)
    try {
      const centerX = r.left + r.width / 2;
      const centerY = r.top + r.height / 2;
      const topEl = document.elementFromPoint(centerX, centerY);
      
      // Element or one of its descendants should be at the point
      if (topEl && (topEl === el || el.contains(topEl))) {
        return true;
      }
      // Special case: element might be in shadow DOM or iframe
      return !topEl || topEl.tagName === 'BODY' || topEl.tagName === 'HTML';
    } catch (e) {
      // If elementFromPoint fails, assume visible
      return true;
    }
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
    return t.replace(/\s+/g, " ").trim();
  }

  function signatureOf(el, label, index) {
    // Stable-ish fingerprint: tag + type + normalized label + index for disambiguation.
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute?.("type") || el.getAttribute?.("role") || "").toLowerCase();
    const key = `${tag}|${type}|${label.toLowerCase().slice(0, 40)}|${index}`;
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      hash = (hash * 31 + key.charCodeAt(i)) & 0xffffffff;
    }
    return "e" + (hash >>> 0).toString(36);
  }

  function collectRoots(root, acc) {
    acc.push(root);
    
    // Scan iframes (same-origin only, cross-origin will throw)
    if (root.querySelectorAll) {
      const iframes = root.querySelectorAll('iframe');
      iframes.forEach(iframe => {
        try {
          if (iframe.contentDocument) {
            collectRoots(iframe.contentDocument, acc);
          }
        } catch (e) {
          // Cross-origin iframe - expected, skip silently
        }
      });
    }
    
    // Scan shadow DOM
    const walker = root.querySelectorAll ? root.querySelectorAll("*") : [];
    walker.forEach((node) => {
      try {
        if (node.shadowRoot) {
          collectRoots(node.shadowRoot, acc);
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
    return false;
  }

  function serialize(el, idCounter) {
    const label = labelFor(el).slice(0, CFG.MAX_TEXT);
    const sig = signatureOf(el, label, idCounter);
    registry.set(sig, el);
    if (el.setAttribute) el.setAttribute("data-cos-sig", sig);

    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute("type") || el.getAttribute("role") || "").toLowerCase();
    const out = {
      id: sig,
      tag,
      type: type || null,
      text: label,
      name: el.getAttribute("name") || null,
      placeholder: el.getAttribute("placeholder") || null,
      value: (el.value != null ? String(el.value) : "").slice(0, CFG.MAX_TEXT),
      required: el.required === true || el.getAttribute("aria-required") === "true",
      disabled: el.disabled === true || el.getAttribute("aria-disabled") === "true",
      checked: el.type === "checkbox" || el.type === "radio" ? !!el.checked : null,
      options: tag === "select"
        ? Array.from(el.options || []).map((o) => o.text.trim()).slice(0, 20)
        : [],
      signature: sig,
    };
    return out;
  }

  function scan() {
    registry.clear();
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
    const key = elements
      .map((e) => `${e.tag}:${e.type}:${e.text}`)
      .join("|")
      .slice(0, 4000);
    let h = 0;
    for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) & 0xffffffff;
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

  COS.Scanner = { scan, diff, stageHash, resolve, isVisible };
})();
