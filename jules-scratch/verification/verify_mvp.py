import re
from playwright.sync_api import sync_playwright, Page, expect

def verify_mvp(page: Page):
    """
    This script verifies the CHS-Twin-Factory MVP.
    It navigates to the frontend, clicks the run button,
    and verifies that a chart is displayed.
    """
    # Listen for all console events and print them
    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))

    # 1. Navigate to the frontend application served by Flask
    page.goto("http://localhost:5001/")

    # 2. Find and click the "Run Simulation" button
    run_button = page.get_by_role("button", name="Run Simulation")
    expect(run_button).to_be_visible()
    run_button.click()

    # 3. Wait for the chart to appear
    # We can wait for the canvas element that Chart.js creates.
    # We'll give it a generous timeout because the simulation might take a few seconds.
    chart_canvas = page.locator("canvas")
    expect(chart_canvas).to_be_visible(timeout=15000)

    # 4. Take a screenshot for visual confirmation
    page.screenshot(path="jules-scratch/verification/verification.png")

# Main execution block
if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_mvp(page)
            print("Verification script completed successfully.")
        except Exception as e:
            print(f"An error occurred during verification: {e}")
        finally:
            browser.close()
