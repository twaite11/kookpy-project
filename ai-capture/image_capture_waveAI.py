from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchFrameException
from webdriver_manager.chrome import ChromeDriverManager
import os
from datetime import datetime
import time

def capture_embedded_video_screenshot_selenium(base_output_dir, interval=600):
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)

    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")
    options.add_argument("--mute-audio")
    options.add_argument("--window-size=1400,800")

    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 30)

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Surf Cam</title>
    </head>
    <body>
        <iframe id="youtube_iframe" width="1310" height="737" src="https://www.youtube.com/embed/VI8Wj5EwoRM" title="Pipeline Cam powered by EXPLORE.org" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    </body>
    </html>
    """
    
    data_url = f"data:text/html;charset=utf-8,{html_content}"

    try:
        driver.get(data_url)
        print("Page loaded.")

        while True:
            # Switch to the iframe
            try:
                iframe_element = wait.until(EC.presence_of_element_located((By.ID, "youtube_iframe")))
                driver.switch_to.frame(iframe_element)
                print("Switched to iframe.")
            except (TimeoutException, NoSuchFrameException) as e:
                print(f"Could not find or switch to iframe: {e}. Retrying...")
                driver.refresh()
                time.sleep(5)
                continue

            # Wait for the video element and get a reference to it
            try:
                video_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
                print("Video element is visible.")
                
                # Check for and click the play button if it appears
                try:
                    play_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-large-play-button")))
                    if play_button.is_displayed():
                        print("Play button found. Clicking it...")
                        play_button.click()
                        time.sleep(2) # Give the video a moment to start
                except TimeoutException:
                    print("Play button not found, assuming video autoplayed.")
                
            except TimeoutException as e:
                print(f"Video element did not load within time limit: {e}. Retrying...")
                driver.switch_to.default_content()
                driver.refresh()
                time.sleep(5)
                continue
                
            # Capture the screenshot of the video element
            try:
                timestamp = datetime.now()
                date_folder = timestamp.strftime("%Y-%m-%d")
                output_folder = os.path.join(base_output_dir, date_folder)
                
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
                
                date_time_str = timestamp.strftime("%Y-%m-%d_%H-%M")
                output_file = os.path.join(output_folder, f"video_screenshot_{date_time_str}.png")
                
                video_element.screenshot(output_file)
                print(f"Captured video screenshot: {output_file}")
            
            except Exception as e:
                print(f"Could not take screenshot: {e}")

            # Switch back to the default content before the next loop iteration
            driver.switch_to.default_content()
            time.sleep(interval)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()

# Example usage:
base_output_directory = r"C:\Users\Tyler\Desktop\surf_imgs\pipeline"
capture_embedded_video_screenshot_selenium(base_output_directory)