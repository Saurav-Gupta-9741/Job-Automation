// Persistent state machine backed by chrome.storage.local so a session survives page
// reloads and external redirects. Keyed by a session id that the background worker can
// inherit into a newly opened ATS tab.
(function () {
  const COS = window.COS;

  const State = {
    session: null, // { id, objective, running, lastStageHash, prevElements }

    async load() {
      // Inherit a session id if the background worker parked one for this tab.
      const tabKeyResp = await chrome.storage.local.get(null);
      let inherited = null;
      for (const k of Object.keys(tabKeyResp)) {
        if (k.startsWith("inherit:")) {
          inherited = tabKeyResp[k];
          await chrome.storage.local.remove(k);
          break;
        }
      }
      const { activeSession, sessionData } = tabKeyResp;
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
      const { sessionData } = await chrome.storage.local.get("sessionData");
      const data = sessionData || {};
      data[this.session.id] = this.session;
      await chrome.storage.local.set({
        sessionData: data,
        activeSession: this.session.id,
      });
    },

    async stop() {
      if (this.session) {
        this.session.running = false;
        await this.save();
      }
      await chrome.storage.local.remove("activeSession");
    },

    isRunning() {
      return !!(this.session && this.session.running);
    },
  };

  COS.State = State;
})();
