import asyncio
from playwright.async_api import async_playwright
import json
import httpx
import time
import random

# Base URL for the FastAPI backend planner
PLANNER_URL = "http://127.0.0.1:8000/api/agent/step"

async def human_like_delay():
    """Simulate human reading/thinking time between actions."""
    await asyncio.sleep(random.uniform(0.5, 2.0))

async def scan_dom(page):
    """
    Extracts interactive elements from the DOM.
    Mimics the logic of the Chrome extension scanner.
    """
    script = """
    () => {
        const INTERACTIVE_TAGS = new Set(["button", "input", "textarea", "select", "a"]);
        const elements = [];
        let idCounter = 0;
        
        function isVisible(el) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) return false;
            const s = window.getComputedStyle(el);
            return s.visibility !== "hidden" && s.display !== "none" && s.opacity !== "0";
        }
        
        const nodes = document.querySelectorAll("*");
        nodes.forEach(el => {
            const tag = el.tagName.toLowerCase();
            if (INTERACTIVE_TAGS.has(tag) && isVisible(el)) {
                let text = el.textContent || el.value || el.getAttribute("placeholder") || el.getAttribute("name") || "";
                text = text.replace(/\\s+/g, " ").trim().substring(0, 50);
                
                const type = (el.getAttribute("type") || el.getAttribute("role") || "").toLowerCase();
                const sig = `e_${idCounter++}_${tag}`;
                el.dataset.cosSig = sig;
                
                elements.push({
                    id: sig,
                    tag: tag,
                    type: type || null,
                    text: text,
                    signature: sig,
                    value: el.value || "",
                    required: el.required || false,
                    disabled: el.disabled || false
                });
            }
        });
        return elements;
    }
    """
    return await page.evaluate(script)

async def execute_action(page, action):
    """Executes a single action returned by the planner."""
    action_type = action.get("type")
    
    if action_type == "click":
        target_id = action.get("target_id")
        if target_id:
            await page.click(f"[data-cos-sig='{target_id}']")
    
    elif action_type == "type":
        target_id = action.get("target_id")
        value = action.get("value", "")
        if target_id:
            # Human-like typing cadence
            await page.type(f"[data-cos-sig='{target_id}']", value, delay=random.randint(50, 150))
            
    elif action_type == "fill_all":
        fields = action.get("fields", [])
        for field in fields:
            tid = field.get("target_id")
            val = field.get("value", "")
            is_select = field.get("select", False)
            if tid:
                if is_select:
                    await page.select_option(f"[data-cos-sig='{tid}']", label=val)
                else:
                    await page.fill(f"[data-cos-sig='{tid}']", val)
                await asyncio.sleep(random.uniform(0.1, 0.4))
                
    elif action_type == "ask_user":
        print(f"\\n[PAUSED - HUMAN IN THE LOOP]\\n{action.get('prompt')}\\n")
        input("Press Enter to resume after resolving in the browser...")
        return "resumed"
        
    elif action_type == "done":
        print("\\n[SUCCESS] Application Complete!\\n")
        return "done"

async def loop_agent(page, session_id):
    """Main execution loop."""
    prev_elements = []
    
    while True:
        await human_like_delay()
        
        # 1. Perceive
        elements = await scan_dom(page)
        url = page.url
        title = await page.title()
        
        payload = {
            "session_id": session_id,
            "url": url,
            "title": title,
            "elements": elements,
            "total_elements": len(elements),
            "stage_hash": "mock_hash", # Simplified for runner
            "objective": "apply"
        }
        
        # 2. Think
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(PLANNER_URL, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                print(f"Backend error: {e}. Retrying in 3s...")
                await asyncio.sleep(3)
                continue
                
        script = data.get("script", [])
        print(f"Stage: {data.get('stage')} | Source: {data.get('source')} | Actions: {len(script)}")
        
        # 3. Act
        for action in script:
            res = await execute_action(page, action)
            if res == "done":
                return
            elif res == "resumed":
                break # Re-scan DOM after user intervention

async def run(url: str):
    print("Starting Stealth Playwright Automation...")
    async with async_playwright() as p:
        # We could use playwright-stealth here if needed
        browser = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Load LinkedIn cookies here if needed
        
        page = await context.new_page()
        await page.goto(url)
        
        # Initialize a unique session
        session_id = f"pw_{int(time.time())}"
        
        print("Agent activated. Starting autonomous loop...")
        await loop_agent(page, session_id)
        
        print("Closing browser in 5 seconds...")
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    import sys
    start_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.linkedin.com"
    asyncio.run(run(start_url))
