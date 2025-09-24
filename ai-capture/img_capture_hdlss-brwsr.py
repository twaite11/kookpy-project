from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
from datetime import datetime
from PIL import Image
import io
import time

def element_has_dimensions(locator):
    def _predicate(driver):
        element = driver.find_element(*locator)
        if element.size['width'] > 0 and element.size['height'] > 0:
            return element
        return False
    return _predicate

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
        <iframe id="youtube_iframe" width="1310" height="737" src="https://www.youtube.com/embed/6hVkLrAmYa0" title="Pacifica Pier and Beach, Pacifica CA 4k Live" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    </body>
    </html>
    """
    
    data_url = f"data:text/html;charset=utf-8,{html_content}"

    try:
        driver.get(data_url)
        
        # This will now successfully find the iframe with the added ID
        iframe_element = wait.until(EC.presence_of_element_located((By.ID, "youtube_iframe")))
        print("Successfully found the iframe.")
        
        driver.switch_to.frame(iframe_element)
        print("Successfully switched to the iframe.")
        
        try:
            play_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-large-play-button")))
            play_button.click()
            print("Successfully clicked the play button.")
        except Exception as e:
            print(f"Could not click play button: {e}. Assuming autoplay or another issue.")

        wait.until(element_has_dimensions((By.TAG_NAME, "video")))
        print("Video element has valid dimensions.")

        while True:
            driver.switch_to.default_content()
            
            timestamp = datetime.now()
            # Create a folder name for the current day
            date_folder = timestamp.strftime("%Y-%m-%d")
            output_folder = os.path.join(base_output_dir, date_folder)
            
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # Create the file name with both date and time
            date_time_str = timestamp.strftime("%Y-%m-%d_%H-%M")
            output_file = os.path.join(output_folder, f"full_screenshot_{date_time_str}.png")
            
            driver.get_screenshot_as_file(output_file)
            print(f"Captured full page screenshot: {output_file}")
            
            driver.switch_to.frame(iframe_element)

            time.sleep(interval)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()

# Example usage:
base_output_directory = r"C:\Users\Tyler\Desktop\surf_imgs"
capture_embedded_video_screenshot_selenium(base_output_directory)
