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

    print("Recherche du groupe :", GROUP_NAME)

    # Cherche le nom du groupe dans la liste des conversations
    chat = page.get_by_text(GROUP_NAME, exact=True)

    if chat.count() == 0:
        print("Groupe non trouvé.")
    else:
        print("Groupe trouvé !")
        chat.first.click()

        page.wait_for_timeout(3000)

        print("\n--- CONTENU DU GROUPE ---\n")
        text = page.locator("body").inner_text()
        print(text[-10000:])

    input("\nAppuie sur Entrée pour fermer...")
    context.close()
