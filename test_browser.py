from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="./whatsapp_profile",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://web.whatsapp.com/")

    print("WhatsApp Web ouvert.")
    print("Connecte ton compte si nécessaire.")

    input("Appuie sur Entrée pour fermer...")
    context.close()
