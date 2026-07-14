// Persistent state machine backed by chrome.storage.local so a session survives page
// reloads and external redirects. Keyed by a session id that the background worker can
// inherit into a newly opened ATS tab.
(function () {
  const COS = window.COS;

  const State = {
    session: null, // { id, objective, running, lastStageHash, prevElements }

    async load() {
      // Get tab ID for tab-scoped session storage
      let tabId = null;
      try {
        const resp = await chrome.runtime.sendMessage({ kind: 'GET_TAB_ID' });
        tabId = resp?.tabId;
      } catch(_) {}
      const tabKey = tabId ? `session:${tabId}` : 'activeSession';
      this._tabKey = tabKey; // Store for save/stop
      
      // Inherit a session id if the background worker parked one for this tab.
      const tabKeyResp = await chrome.storage.local.get(null);
      let inherited = null;
      for (const k of Object.keys(tabKeyResp)) {
        if (k.startsWith("inherit:") && (!tabId || k === `inherit:${tabId}`)) {
          inherited = tabKeyResp[k];
          await chrome.storage.local.remove(k);
          break;
        }
      }
      const activeSession = tabKeyResp[tabKey] || tabKeyResp['activeSession'];
      const sessionData = tabKeyResp.sessionData;
      const id = inherited || activeSession || null;
      this.session = (id && sessionData && sessionData[id]) || null;
      if (this.session && inherited) {
        // Resuming after a redirect -> keep running.
        this.session.running = true;
        await this.save();
      }

      // Cleanup stale sessions (>24h old) to prevent storage bloat
      if (sessionData && typeof sessionData === "object") {
        const now = Date.now();
        const staleThreshold = 24 * 60 * 60 * 1000; // 24 hours
        let cleaned = false;
        for (const [sid, data] of Object.entries(sessionData)) {
          if (sid === id) continue; // Don't clean the active one
          const ts = parseInt(sid.replace("sess-", "").split("-")[0], 36);
          if (now - ts > staleThreshold) {
            delete sessionData[sid];
            cleaned = true;
          }
        }
        if (cleaned) {
          await chrome.storage.local.set({ sessionData });
        }
      }

      return this.session;
    },

    async start(objective) {
      const id = COS.uuid();
      this.session = {
        id,
        objective: objective || "apply",
        running: true,
        lastStageHash: "",
        prevElements: [],
        pendingHandoff: null,
      };
      await this.save();
      return this.session;
    },

    async save() {
      if (!this.session) return;
      const tabKey = this._tabKey || 'activeSession';
      const { sessionData } = await chrome.storage.local.get("sessionData");
      const data = sessionData || {};
      data[this.session.id] = this.session;
      const storageUpdate = { sessionData: data };
      storageUpdate[tabKey] = this.session.id;
      // Also write to activeSession for backward compatibility
      storageUpdate.activeSession = this.session.id;
      await chrome.storage.local.set(storageUpdate);
    },

    async stop() {
      if (this.session) {
        this.session.running = false;
        await this.save();
      }
      const tabKey = this._tabKey || 'activeSession';
      const keysToRemove = ['activeSession'];
      if (tabKey !== 'activeSession') keysToRemove.push(tabKey);
      await chrome.storage.local.remove(keysToRemove);
    },

    isRunning() {
      return !!(this.session && this.session.running);
    },
  };

  COS.State = State;
})();
