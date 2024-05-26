import pickle
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import StaleElementReferenceException , TimeoutException
import os

# Load cookies from file
def load_cookies(driver, filepath):
    try:
        with open(filepath, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                try:
                    print(f"Adding cookie: {cookie}")
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie {cookie}: {e}")
        print("Cookies loaded successfully.")
    except Exception as e:
        print(f"Error loading cookies: {e}")

# Setup undetected ChromeDriver
options = uc.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.headless = False  # Set to False for debugging

print("Initializing WebDriver...")
try:
    driver = uc.Chrome(options=options)
    print("WebDriver initialized successfully.")
except Exception as e:
    print(f"Error initializing WebDriver: {e}")
    raise

# Navigate to ChatGPT login page
print("Navigating to ChatGPT login page...")
try:
    driver.get("https://chat.openai.com/auth/login")
    print("Page loaded successfully.")
except Exception as e:
    print(f"Error loading page: {e}")
    driver.quit()
    raise

# Load cookies
load_cookies(driver, "cookies.pkl")

# Refresh the page to apply cookies
driver.refresh()

# Function to post the screenshot and ask a question to OpenAI ChatGPT
def post_chart_to_openai_chat(file_path: str, question: str):
    try:
        # Convert relative file path to absolute file path
        absolute_file_path = os.path.abspath(file_path)

        # Locate the file input element and upload the screenshot
        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="file"]'))
        )
        file_input.send_keys(absolute_file_path)

        # Wait for the file to be uploaded and visible in the chat
        time.sleep(5)  # Adjust the sleep time if necessary

        # Assuming the text input area is still available after uploading the file
        text_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="prompt-textarea"]'))
        )
        text_input.send_keys(question)

        # Wait for the submit button to appear before clicking
        submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/main/div[1]/div[2]/div[1]/div/form/div/div[2]/div/div/button'))
        )
        submit_button.click()

        # Wait for the specified element to appear, indicating the end of the response
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/div[2]/main/div[1]/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div[2]'))
        )

        # Take a screenshot of the entire screen
        screen_screenshot = driver.get_screenshot_as_png()
        with open("response_element_screenshot.png", "wb") as file:
            file.write(screen_screenshot)
        print("Screenshot of the entire screen saved as 'response_element_screenshot.png'")

        # Wait for the response to appear
        response_element = WebDriverWait(driver, 30).until(
            # EC.visibility_of_element_located((By.XPATH, '//*[@id="__next"]/div[1]/div[2]/main/div[1]/div[1]/div/div/div/div/div[3]/div/div/div[2]'))
            EC.visibility_of_element_located(
                (By.XPATH, '/html/body/div[1]/div[1]/div[2]/main/div[1]/div[1]/div/div/div/div/div[3]/div/div/div[2]'))
        )

        # Ensure the response is fully loaded by checking for the presence of text
        while True:
            try:
                response_html = response_element.get_attribute("innerHTML").strip()
                if response_html:
                    response_text = response_element.get_attribute("textContent").strip()
                    break
            except StaleElementReferenceException:
                # Re-find the element in case it becomes stale
                response_element = driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/main/div[1]/div[1]/div/div/div/div/div[3]/div/div/div[2]')
            time.sleep(1)  # Wait for 1 second before checking again

        # Debugging: Print the response element found
        print(f"Response element found: {response_element}")

        # Retrieve the response text correctly
        print("Response from OpenAI Chat:", response_text)
        return response_text

    except TimeoutException:
        print("Timed out waiting for the response.")
        try:
            # Take a screenshot of the entire screen in case of timeout
            screen_screenshot = driver.get_screenshot_as_png()
            with open("response_element_screenshot.png", "wb") as file:
                file.write(screen_screenshot)
            print("Screenshot of the entire screen saved as 'response_element_screenshot.png'")
        except Exception as e:
            print(f"An error occurred while taking the screenshot: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Step 1: Capture TradingView chart
# tradingview_chart_url = "https://www.tradingview.com/chart/lV1rbUkf/"
screenshot_path = "tradingview_chart.png"
# capture_tradingview_chart(tradingview_chart_url, screenshot_path)

# Step 2 and Step 3: Post the screenshot and ask a question to OpenAI ChatGPT
question = """Analyze the following chart and predict the trend, entry points, exit points, and stop loss based on the trend. 
Can you share the output as per your analysis. Provide output in below format.
<Coin name from chart>
LONG
Entry : <range1> - <range2>
Leverage : Cross 20X
Target 1 - 
Target 2 - 
Target 3 - 
Stop Loss :"""
chart_analysis = post_chart_to_openai_chat(screenshot_path, question)
print(chart_analysis)

# Close the driver
# driver.quit()