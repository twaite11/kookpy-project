import os
import io
import time
from datetime import datetime
from PIL import Image

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capture_embedded_video_screenshot_selenium(embed_url, output_dir, interval=600):
    """
    Captures a screenshot of an embedded video frame at a regular interval.

    This function uses Selenium to open a headless Chrome browser, inject a video iframe,
    and then continuously take and save screenshots of the video frame.

    Args:
        embed_url (str): The URL of the embedded video (e.g., a YouTube embed link).
        output_dir (str): The directory where screenshots will be saved. The function
                          will create this directory if it does not exist.
        interval (int, optional): The time in seconds to wait between screenshots.
                                  Defaults to 600 (10 minutes).
    """
    # Create the output directory if it doesn't already exist.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- WebDriver Configuration ---
    # This section sets up the Chrome browser instance.

    # 1. Specify the path to your ChromeDriver executable.
    # IMPORTANT: You must download the chromedriver.exe that matches your Chrome browser version.
    # The path provided here is an example and should be replaced with your actual path.
    chromedriver_path = r"C:\Users\Tyler\Desktop\chromedriver.exe"
    service = Service(executable_path=chromedriver_path)

    # 2. Configure the Chrome options.
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')       # Runs the browser in the background without a UI.
    options.add_argument('--disable-gpu')    # Disables GPU hardware acceleration for headless mode.
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")
    options.add_argument("--mute-audio")     # Mutes audio from the video.

    # Initialize the WebDriver with the configured service and options.
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Step 1: Create and Inject the Iframe
        # The script navigates to a blank page and uses JavaScript to dynamically
        # create and add an iframe element containing the embedded video.
        driver.get("about:blank")
        driver.execute_script(f"""
        var iframe = document.createElement('iframe');
        iframe.width = '781';
        iframe.height = '439';
        iframe.src = '{embed_url}';
        iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
        iframe.allowFullscreen = true;
        document.body.appendChild(iframe);
        """)

        # Step 2: Wait for the Iframe to Load and Switch Focus
        # We wait until the iframe is present on the page. Once it is, we switch
        # the WebDriver's focus to it so we can interact with its content.
        wait = WebDriverWait(driver, 20)
        iframe = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe")))
        driver.switch_to.frame(iframe)

        # Step 3: Attempt to Click the Play Button
        # The script attempts to find and click the play button to ensure the video
        # is playing. This is often necessary for live streams or videos that don't
        # autoplay. The focus is then switched back to the main document.
        try:
            play_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytp-large-play-button")))
            play_button.click()
            driver.switch_to.default_content()
        except Exception as e:
            # If the play button isn't found or clickable, it might be an ad or
            # a different UI, and we can continue.
            print(f"Could not click play button: {e}")
            driver.switch_to.default_content()

        # Step 4: Continuous Screenshot Loop
        # This loop runs indefinitely, taking a screenshot at the specified interval.
        while True:
            try:
                # Re-locate and switch to the iframe to ensure focus.
                iframe = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe")))
                driver.switch_to.frame(iframe)

                # Find the video element within the iframe.
                video_frame = driver.find_element(By.TAG_NAME, "video")
                video_frame_location = video_frame.location
                video_frame_size = video_frame.size

                # Switch focus back to the main document to take a full-page screenshot.
                driver.switch_to.default_content()

                # Take the full screenshot and use Pillow to crop it to the video frame's dimensions.
                img = Image.open(io.BytesIO(driver.get_screenshot_as_png()))
                left = video_frame_location['x']
                top = video_frame_location['y']
                right = left + video_frame_size['width']
                bottom = top + video_frame_size['height']
                img = img.crop((left, top, right, bottom))

                # Create a file name based on the current date and time.
                timestamp = datetime.now()
                date_str = timestamp.strftime("%d-%m-%Y")
                time_str = timestamp.strftime("%H-%M")
                output_file = os.path.join(output_dir, f"{date_str}.{time_str}.sharppark1.png")

                # Save the cropped screenshot.
                img.save(output_file)
                print(f"Captured video frame screenshot: {output_file}")

            except Exception as e:
                # Log any errors that occur during the screenshot process.
                print(f"Error capturing video frame screenshot: {e}")
                driver.switch_to.default_content()

            # Wait for the specified interval before the next capture.
            time.sleep(interval)

    except Exception as e:
        # Catch any exceptions that might occur during the initial setup.
        print(f"An error occurred: {e}")
    finally:
        # Ensure the browser is closed, even if an error occurs.
        driver.quit()

# --- Example Usage ---
if __name__ == "__main__":
    # Specify the embedded video URL and the output directory.
    # The URL should be for an embedded video, e.g., from YouTube's "Embed" option.
    embed_url = "https://www.youtube.com/embed/hEFZzMgGnCs"
    output_directory = r"C:\Users\Tyler\Desktop\surf_imgs"

    # Call the function to begin capturing screenshots.
    capture_embedded_video_screenshot_selenium(embed_url, output_directory)
