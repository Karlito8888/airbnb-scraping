import os
import webbrowser
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

SBR_WS_CDP = os.getenv('SBR_WS_CDP')

def open_debug_view(page):
    client = page.context.new_cdp_session(page)
    frame_tree = client.send('Page.getFrameTree', {})
    frame_id = frame_tree['frameTree']['frame']['id']
    inspect = client.send('Page.inspect', {'frameId': frame_id})
    inspect_url = inspect['url']
    webbrowser.open(inspect_url)

def route_intercept(route):
    if route.request.resource_type == "image":
        return route.abort()
    return route.continue_()

def handle_popup(page):
    try:
        print("Waiting for 'Continuer sans accepter' button")
        button = page.locator('//button[contains(text(), "Continuer sans accepter")]')
        button.wait_for(state='visible', timeout=60000)
        print("Clicking 'Continuer sans accepter' button")
        button.click()
    except Exception as e:
        print(f"Erreur lors du clic sur le bouton 'Continuer sans accepter': {e}")

    try:
        print("Waiting for 'Fermer' button")
        close_button = page.get_by_label("Fermer")
        close_button.wait_for(state='visible', timeout=6000)
        print("Clicking 'Fermer' button")
        close_button.click()
    except Exception as e:
        print(f"Erreur lors du clic sur le bouton 'Fermer': {e}")

def perform_search(page):
    try:
        page.get_by_test_id("structured-search-input-field-query").click()
        page.get_by_test_id("structured-search-input-field-query").fill("Rio de Janeiro")
        page.get_by_test_id("option-0").click()
        page.get_by_test_id("expanded-searchbar-dates-months-tab").click()
        page.locator("span:nth-child(6)").first.click()
        page.get_by_test_id("structured-search-input-field-guests-button").click()
        page.get_by_test_id("stepper-adults-increase-button").click()
        page.get_by_test_id("structured-search-input-search-button").click()
    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")

def navigate_pages(page):
    page_number = 1

    while True:
        try:
            print(f"Navigating to page {page_number}")
            next_page_button = page.get_by_label("Suivant", exact=True)
            if next_page_button.get_attribute("aria-disabled") == 'true':
                print("No more pages to navigate. Stopping.")
                break

            page_number += 1
            print("Clicking 'Suivant' button")
            next_page_button.click()
            page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Erreur lors de la navigation des pages: {e}")
            break

def run(pw, bright_data=False, headless=False):
    print("Connecting to Scraping Browser")
    try:
        if bright_data:
            browser = pw.chromium.connect_over_cdp(SBR_WS_CDP)
        else:
            browser = pw.chromium.launch(headless=headless)

        context = browser.new_context()
        context.set_default_timeout(60000)
        page = context.new_page()
        # page.route("**/*", route_intercept)

        if bright_data and not headless:
            open_debug_view(page)

        url = "https://www.airbnb.fr/"
        print(f"Navigating to {url}")
        page.goto(url)
        handle_popup(page)
        perform_search(page)
        navigate_pages(page)

        # html_content = page.content()
        # soup = BeautifulSoup(html_content, 'html.parser')
        # print(soup.prettify())

    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if 'browser' in locals():
            print("Closing the browser")
            browser.close()

if __name__ == '__main__':
    with sync_playwright() as playwright:
        run(pw=playwright, bright_data=False, headless=False)
