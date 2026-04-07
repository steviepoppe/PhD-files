import time
import pandas as pd
import csv

from selenium import webdriver 
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By 
from selenium.webdriver.chrome.options import Options
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException


def scrape_short_details(short_url, driver):

    results = []

    driver.get(short_url)
    driver.maximize_window()

    time.sleep(3)

    try:
        # Wait until the cookie banner shows up and click "Reject all"
        reject_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button//span[contains(text(), 'Reject all')]")
            )
        )
        reject_button.click()
        print("✅ Rejected cookies.")
    except Exception as e:
        print("⚠️ No cookie popup or button not found:", e)

    print("waiting")
    time.sleep(4)
    print("waiting done")


    # wait for the overlay container to appear
    overlay = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-reel-player-overlay-renderer"))
    )

    # Background music
    try:
        music_elem = overlay.find_element(
            By.CSS_SELECTOR,
            "reel-sound-metadata-view-model .ytMarqueeScrollPrimaryString"
        )
        background_music = music_elem.text
    except:
        background_music = None

    # wait for the overlay container to appear
    overlay_comments = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".ytwReelActionBarViewModelHost"))
    )
    # Comments button
    try:
        comments_elem = overlay_comments.find_elements(
            By.CSS_SELECTOR,
            ".yt-spec-button-shape-with-label__label"
        )
        comments_count = comments_elem[2].text
    except:
        comments_count = None

    # Click the three dots 
    try:

        # Hover over the video player container to reveal the overlay
        video_overlay = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "ytd-reel-player-overlay-renderer")
            )
        )
        ActionChains(driver).move_to_element(video_overlay).perform()
        time.sleep(1)


        overlay = driver.find_element(By.CSS_SELECTOR, "ytd-reel-video-renderer")
        ActionChains(driver).move_to_element(overlay).perform()
        time.sleep(0.4)

        # 3️⃣ Now find the actual More Actions button (the one inside yt-button-shape)
        more_actions_btn = overlay.find_element(
            By.XPATH,
            ".//yt-button-shape[@id='button-shape']//button[@aria-label='More actions']"
        )

        # Click it using JavaScript
        driver.execute_script("arguments[0].click();", more_actions_btn)
        time.sleep(1)

        # Click Description menu item
        desc_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//tp-yt-paper-item[contains(., 'Description')]")
            )
        )
        driver.execute_script("arguments[0].click();", desc_btn)
        time.sleep(2)

        # Step 2: Click the "Description" button
        desc_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//tp-yt-paper-item[contains(., 'Description')]"))
        )
        driver.execute_script("arguments[0].click();", desc_btn)
        time.sleep(2)

    except Exception as e:
        print("Could not open description:", e)



    # Execute JS to extract info from Shadow DOM
    data = driver.execute_script("""
        const container = document.querySelector('ytd-structured-description-content-renderer');
        if (!container) return null;
        const shadow = container.shadowRoot || container;

        const result = {};

        // Title
        const title_elem = shadow.querySelector("#title span");
        result.title = title_elem ? title_elem.innerText : null;

        // Description text
        const desc_elem = shadow.querySelector("#snippet-text #plain-snippet-text");
        result.description = desc_elem ? desc_elem.innerText : null;

        // Factoids (likes, comments, views, date)
        const factoids = shadow.querySelector("#factoids");
        if (factoids) {
            const likes_elem = factoids.querySelector("factoid-renderer div[aria-label*='likes'] span.yt-core-attributed-string");
            result.likes = likes_elem ? likes_elem.innerText : null;

            const views_elem = factoids.querySelector("view-count-factoid-renderer factoid-renderer span.yt-core-attributed-string");
            result.views = views_elem ? views_elem.innerText : null;

            // Combine day/month + year
            const last_factoid = factoids.querySelectorAll("factoid-renderer");
            if (last_factoid.length > 0) {
                const date_elem = last_factoid[last_factoid.length - 1];
                const day_month = date_elem.querySelector("span.ytwFactoidRendererValue span.yt-core-attributed-string");
                const year = date_elem.querySelector("span.ytwFactoidRendererLabel span.yt-core-attributed-string");
                result.upload_date = day_month && year ? `${day_month.innerText} ${year.innerText}` : null;
            } else {
                result.upload_date = null;
            }
        }

        // How this content was made
        const how_elem = shadow.querySelector("how-this-was-made-section-view-model .ytwHowThisWasMadeSectionViewModelBodyHeader span");
        result.how_made = how_elem ? how_elem.innerText : null;

        return result;
    """)

    if data is None:
        data = {}


    # Append result
    results.append({
        "Title": data['title'],
        "Likes": data['likes'],
        "Views": data['views'],
        "UploadDate": data['upload_date'],
        "Comments": comments_count,
        "URL": short_url,
        "BackgroundMusic": background_music,
        "Description": data['description'],
        "howMade": data['how_made']
    })

    return results


if __name__ == "__main__":

    csv_file = "youtube_shorts_data.csv"

    all_rows = []

    driver =  webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    for u in urls:
        print(f"\n=== Scraping {u} ===")
        data = scrape_short_details(u, driver)
        print(data)
        all_rows.extend(data)


    # --- Save to CSV ---
    df = pd.DataFrame(all_rows)
    try:
        existing_df = pd.read_csv(csv_file, encoding="utf-8", quoting=csv.QUOTE_ALL)
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        pass  # file doesn't exist yet

    df.to_csv(
        csv_file,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_ALL,
        escapechar="\\",
        lineterminator="\n"
    )
    print(f"Saved {len(all_rows)} entries to {csv_file}")

    driver.quit()