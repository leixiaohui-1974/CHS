import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # 1. Navigate to the application
        await page.goto("http://localhost:3000")

        # 2. Wait for the device cards to be visible
        await expect(page.get_by_text("sluice_gate_03")).to_be_visible(timeout=10000)

        # Take a screenshot of the initial state
        await page.screenshot(path="jules-scratch/verification/initial_state.png")

        # 3. Simulate a decision request from the backend
        decision_request = {
            "event": "decision_request",
            "device_id": "sluice_gate_03",
            "message": "Upstream water level is too high, please select an action:",
            "options": [
                {"label": "Open to 50%", "action": {"gate_opening": 0.5}},
                {"label": "Open to 100%", "action": {"gate_opening": 1.0}}
            ]
        }

        # This is a bit of a hack. We're using evaluate to manually trigger the onmessage handler
        # of the websocket service. This is necessary because we don't have a real backend.
        await page.evaluate(f"""
            window.mockWebSocketMessage({str(decision_request)})
        """)

        # 4. Verify that the decision UI is visible
        await expect(page.get_by_text("Upstream water level is too high, please select an action:")).to_be_visible()
        await expect(page.get_by_role("button", name="Open to 50%")).to_be_visible()
        await expect(page.get_by_role("button", name="Open to 100%")).to_be_visible()

        # 5. Take a screenshot of the decision UI
        await page.screenshot(path="jules-scratch/verification/decision_ui.png")

        # 6. Click the "Open to 50%" button
        await page.get_by_role("button", name="Open to 50%").click()

        # 7. Verify that the decision UI is no longer visible
        await expect(page.get_by_text("Upstream water level is too high, please select an action:")).not_to_be_visible()

        # 8. Take a screenshot to confirm the UI has been reset
        await page.screenshot(path="jules-scratch/verification/final_state.png")

        await browser.close()

# In order to run this, we need to inject a mock function into the window object
# that the playwright script can call. We can't do that from the playwright script
# itself, so we need to modify the application code to include it.
#
# I will add a small script to `public/index.html` to do this.
#
# This is not ideal, but it's the only way to test this functionality without a real backend.

if __name__ == '__main__':
    asyncio.run(main())
