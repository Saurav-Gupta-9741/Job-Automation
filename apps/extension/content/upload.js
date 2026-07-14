// Resume upload without touching the OS file picker.
// Strategy: fetch the resume (base64) from the backend, build a real File, and either set
// it directly on an <input type=file>, or simulate a physical drag-and-drop onto a custom
// dropzone/button (Cutshort-style). The native picker is never opened.
(function () {
  const COS = window.COS;

  let cachedFile = null;

  async function getResumeFile() {
    if (cachedFile) return cachedFile;
    const resp = await chrome.runtime.sendMessage({ kind: "RESUME" });
    if (!resp || !resp.ok) throw new Error(resp?.error || "resume fetch failed");
    const { filename, mime, base64 } = resp.data;
    const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
    cachedFile = new File([bytes], filename || "resume.pdf", {
      type: mime || "application/pdf",
    });
    return cachedFile;
  }

  function setNativeInput(input, file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    // Use Object.defineProperty for React compatibility
    Object.defineProperty(input, 'files', { value: dt.files, writable: true });
    input.files = dt.files;
    // Dispatch framework-aware events
    const inputEvent = new Event('input', { bubbles: true, cancelable: true, composed: true });
    Object.defineProperty(inputEvent, 'target', { value: input });
    input.dispatchEvent(inputEvent);
    const changeEvent = new Event('change', { bubbles: true, cancelable: true, composed: true });
    Object.defineProperty(changeEvent, 'target', { value: input });
    input.dispatchEvent(changeEvent);
    // React-specific: trigger native input event setter
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    if (nativeInputValueSetter) {
      nativeInputValueSetter.call(input, input.value);
    }
    return true;
  }

  async function simulateDrop(target, file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    
    // Full drag sequence with proper timing and positioning
    const rect = target.getBoundingClientRect();
    const clientX = rect.left + rect.width / 2;
    const clientY = rect.top + rect.height / 2;
    
    const events = [
      'dragstart',
      'drag',
      'dragenter',
      'dragover',
      'drop',
      'dragend'
    ];
    
    for (const type of events) {
      const opts = { 
        bubbles: true, 
        cancelable: true, 
        dataTransfer: dt,
        clientX,
        clientY,
        screenX: clientX,
        screenY: clientY
      };
      
      const event = new DragEvent(type, opts);
      target.dispatchEvent(event);
      
      // Fire multiple dragover events like real drag behavior
      if (type === 'dragover') {
        for (let i = 0; i < 3; i++) {
          await COS.sleep(50);
          target.dispatchEvent(new DragEvent(type, opts));
        }
      }
      
      await COS.sleep(100);
    }
    
    // Also try triggering change event on any nearby file input
    const nearbyInput = target.closest?.('form')?.querySelector?.('input[type="file"]') ||
                       target.querySelector?.('input[type="file"]');
    if (nearbyInput) {
      setNativeInput(nearbyInput, file);
    }
    
    return true;
  }

  // Given the button/element the planner told us to use for upload, attach the resume.
  async function uploadResume(triggerEl) {
    const file = await getResumeFile();

    // 1) A real file input anywhere near the trigger (or on the page) wins.
    let input = null;
    if (triggerEl) {
      input = triggerEl.closest?.("form")?.querySelector?.('input[type="file"]');
    }
    if (!input) input = document.querySelector('input[type="file"]');
    // Also pierce shadow roots for the file input.
    if (!input) input = deepQueryFileInput(document);

    if (input) return setNativeInput(input, file);

    // 2) No input -> custom dropzone. Simulate a physical drop on the trigger.
    if (triggerEl) return simulateDrop(triggerEl, file);

    throw new Error("no file input or dropzone found for resume upload");
  }

  function deepQueryFileInput(root) {
    const direct = root.querySelector?.('input[type="file"]');
    if (direct) return direct;
    const all = root.querySelectorAll ? root.querySelectorAll("*") : [];
    for (const node of all) {
      if (node.shadowRoot) {
        const found = deepQueryFileInput(node.shadowRoot);
        if (found) return found;
      }
    }
    return null;
  }

  COS.Upload = { uploadResume };
})();
