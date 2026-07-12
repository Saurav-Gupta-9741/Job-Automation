// Shared constants for the content scripts. Attached to window so every module sees them.
window.COS = window.COS || {};
window.COS.CONFIG = {
  // Pacing: human-like delays between actions to avoid bot-detection and let the DOM settle.
  MIN_ACTION_DELAY_MS: 700,
  MAX_ACTION_DELAY_MS: 1600,
  // Delay after navigation / DOM mutation before we re-scan.
  SETTLE_MS: 900,
  // Max elements to send per step (token discipline mirrors the backend).
  MAX_ELEMENTS: 80,
  // Max characters of visible text per element.
  MAX_TEXT: 60,
  // Poll interval when idle / waiting.
  IDLE_MS: 1500,
  // Automatically move to the next job in the search list after finishing one
  BULK_APPLY_ENABLED: false,
  // Dry run mode: log actions without executing (for testing)
  DRY_RUN_MODE: false,
};

// Small helpers.
window.COS.rand = (a, b) => a + Math.floor(Math.random() * (b - a));
window.COS.sleep = (ms) => new Promise((r) => setTimeout(r, ms));
window.COS.uuid = () =>
  "sess-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8);
