# Headless Browser Video Screenshot
This Python script uses Selenium to open a headless (invisible) Chrome browser, capture a screenshot of an embedded video frame, and save the image to a specified directory. This is useful for monitoring live streams or capturing periodic frames from a specific video.

## Prerequisites
* Python 3.6+:
Ensure Python is installed on your system.

* Google Chrome: The browser executable is required.

* ChromeDriver: 
You must have the chromedriver.exe executable, which acts as the bridge between your script and the browser.  It is crucial to use a version of ChromeDriver that matches your version of Google Chrome.

* Required Python Libraries:
Install the necessary libraries using pip:

`pip install selenium Pillow`

## How It Works
The script operates in four main steps:

* Browser Initialization:
It sets up a headless Chrome instance with options to run in the background without a graphical user interface.

* Iframe Injection:
It navigates to a blank page and uses JavaScript to dynamically create and inject an <iframe> element with your video URL.

* Video Interaction:
It attempts to click the video's play button to ensure the stream is active.

* Continuous Capture:
It enters a loop that periodically captures a full-page screenshot and then crops it to the exact dimensions of the video frame, saving the resulting image with a timestamp.

## Usage
Set Paths: Open the script in your code editor and update the chromedriver_path variable to the correct location of your ChromeDriver executable.

`chromedriver_path = r"C:\Users\etc\Desktop\chromedriver.exe"`

Define Video and Output: In the `if __name__ == "__main__":` block at the bottom of the script, specify the embed_url of the video and the output_directory where you want to save the screenshots.

`embed_url = "https://www.youtube.com/embed/hEFZzMgGnCs"
output_directory = r"C:\Users\Tyler\Desktop\surf_imgs"`

Run the Script: Execute the Python file from your terminal.

`python your_script_name.py`

The script will begin capturing and saving images to the specified directory at the configured interval.