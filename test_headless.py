from playwright.sync_api import sync_playwright

GROUP_NAME = "Benjamines Alevines TriCorrecas"

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir="./whatsapp_profile",
        headless=True
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto("https://web.whatsapp.com/")

    page.wait_for_timeout(7000)

    print("Titre :", page.title())
    print("URL :", page.url)

    chat = page.get_by_text(GROUP_NAME, exact=True)

    if chat.count() > 0:
        print("WhatsApp connecté et groupe trouvé !")
    else:
        print("⚠️ Groupe non trouvé.")

    context.close()
