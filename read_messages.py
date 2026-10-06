from playwright.sync_api import sync_playwright

GROUP_NAME = "Benjamines Alevines TriCorrecas"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="./whatsapp_profile",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://web.whatsapp.com/")
    page.wait_for_timeout(5000)

    # Ouvrir le groupe
    chat = page.get_by_text(GROUP_NAME, exact=True)

    if chat.count() == 0:
        print("Groupe non trouvé.")
        input("Entrée pour fermer...")
        context.close()
        exit()

    chat.first.click()
    page.wait_for_timeout(3000)

    # Chercher les éléments correspondant aux messages
    messages = page.locator('[data-pre-plain-text]')

    print(f"\nNombre de messages détectés : {messages.count()}\n")

    for i in range(messages.count()):
        message = messages.nth(i)

        metadata = message.get_attribute("data-pre-plain-text")
        text = message.inner_text()

        print("=" * 60)
        print("METADATA :", metadata)
        print("MESSAGE  :", text[:1000])

    input("\nAppuie sur Entrée pour fermer...")
    context.close()
