from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="./whatsapp_profile",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto("https://web.whatsapp.com/")
    page.wait_for_timeout(5000)

    print("\n--- TEXTES VISIBLES ---\n")

    text = page.locator("body").inner_text()

    print(text[:10000])

    input("\nAppuie sur Entrée pour fermer...")
    context.close()
