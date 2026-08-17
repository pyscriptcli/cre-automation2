# scripts/wake_apps.py

from playwright.async_api import async_playwright
import asyncio
import sys

# 👇 REPLACE THESE WITH YOUR ACTUAL APP URLS
APP_URLS = [
    "https://open-node.streamlit.app",
    "https://project-apex.streamlit.app",
    "https://trs-site-report.streamlit.app",
    "https://primephilippines2026midyearpropertymarketreport.streamlit.app",
]

async def wake_up_app(url):
    async with async_playwright() as p:
        # Launch a headless Chromium browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"🌐 Visiting: {url}")
        
        try:
            # Navigate to the app, wait for the DOM to load
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait a moment for the page to settle
            await page.wait_for_timeout(3000)
            
            # Check if the wake-up button exists
            wake_button = page.get_by_role("button", name="Yes, get this app back up!")
            
            if await wake_button.count() > 0:
                print(f"🔄 App is sleeping! Clicking wake button for {url}")
                await wake_button.click()
                # Wait up to 90 seconds for the app to fully boot
                await page.wait_for_timeout(90000)
                print(f"✅ App should now be awake: {url}")
            else:
                print(f"✅ App is already awake: {url}")
                
        except Exception as e:
            print(f"❌ Error with {url}: {e}")
        finally:
            await browser.close()

async def main():
    print(f"🚀 Starting wake-up cycle for {len(APP_URLS)} apps...")
    for url in APP_URLS:
        await wake_up_app(url)
    print("🏁 All apps processed.")

if __name__ == "__main__":
    asyncio.run(main())
