// Service worker: the only component allowed to talk to the backend (bypasses CORS
// via host_permissions) and to track redirect tabs so a session survives navigation.

const BACKEND = "http://127.0.0.1:8000";

// --- CSRF/Security token extraction ----------------------------------------

async function extractSecurityTokens(tabId) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: () => {
        // Extract common CSRF tokens
        const csrf = document.querySelector('input[name="_csrf"]')?.value ||
                     document.querySelector('input[name="csrf_token"]')?.value ||
                     document.querySelector('meta[name="csrf-token"]')?.content ||
                     document.querySelector('meta[name="_csrf"]')?.content;
        
        // Extract from cookies
        const cookieMatch = document.cookie.match(/XSRF-TOKEN=([^;]+)/);
        const xsrfToken = cookieMatch ? cookieMatch[1] : null;
        
        // LinkedIn specific tokens
        const jsessionId = document.cookie.match(/JSESSIONID=([^;]+)/)?.[1];
        
        return { 
          csrf, 
          xsrfToken, 
          jsessionId,
          cookies: document.cookie 
        };
      }
    });
    
    return results[0]?.result || {};
  } catch (e) {
    console.warn('Failed to extract security tokens:', e);
    return {};
  }
}

// --- backend bridge ----------------------------------------------------------

async function backendStep(payload, sender) {
  // Extract security tokens from the page
  const tokens = await extractSecurityTokens(sender.tab.id);
  payload.security_tokens = tokens;
  
  const res = await fetch(`${BACKEND}/api/agent/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`backend ${res.status}`);
  return res.json();
}

async function fetchResume() {
  const res = await fetch(`${BACKEND}/api/resume`);
  if (!res.ok) throw new Error(`resume ${res.status}`);
  return res.json(); // { filename, mime, base64 }
}

// --- message router ----------------------------------------------------------

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    try {
      if (msg.kind === "STEP") {
        sendResponse({ ok: true, data: await backendStep(msg.payload, sender) });
      } else if (msg.kind === "RESUME") {
        sendResponse({ ok: true, data: await fetchResume() });
      } else if (msg.kind === "SCREENSHOT") {
        chrome.tabs.captureVisibleTab(null, { format: "jpeg", quality: 50 }, (dataUrl) => {
          if (chrome.runtime.lastError) {
             sendResponse({ ok: false, error: chrome.runtime.lastError.message });
          } else {
             sendResponse({ ok: true, data: dataUrl });
          }
        });
        return; // async callback handles response
      } else {
        sendResponse({ ok: false, error: "unknown message" });
      }
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
  })();
  return true; // async response
});

// --- redirect / new-tab session hand-off ------------------------------------
// When an external "Apply" opens a new tab, carry the active session id to it so
// the agent resumes the same application on the ATS page.

chrome.tabs.onCreated.addListener(async (tab) => {
  try {
    const { activeSession } = await chrome.storage.local.get("activeSession");
    if (activeSession && tab.id != null) {
      await chrome.storage.local.set({ [`inherit:${tab.id}`]: activeSession });
    }
  } catch (_) {}
});
