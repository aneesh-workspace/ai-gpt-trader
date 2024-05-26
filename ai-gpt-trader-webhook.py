import pickle
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import os
from PIL import Image
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import io
from telegram.error import TelegramError
import re
import asyncio
from flask import Flask, request, jsonify

app = Flask(__name__)


# Set up Telegram Bot
bot_token = "5675379828:AAHjRijYM1mF1WaIK2egcMg4vXp4yn9pYyY"
chat_id = "-1001819154166"
bot = Bot(token=bot_token)


# Function to get TradingView chart URL
def get_tradingview_chart_url(symbol, timeframe):
    return f"https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}&interval={timeframe}"


# Function to take TradingView chart screenshot using Firefox
def capture_tradingview_chart(url: str, file_path: str):
    try:
        # Initialize the Firefox WebDriver
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        gecko_driver_path = GeckoDriverManager().install()
        mozilla_driver = webdriver.Firefox(service=Service(gecko_driver_path), options=options)

        # Capture the chart screenshot
        mozilla_driver.get(url)
        time.sleep(30)  # Allow chart to load
        screenshot = mozilla_driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))
        image.save(file_path)
        print(f"Chart screenshot saved to {file_path}")
        mozilla_driver.quit()
    except Exception as e:
        print(f"Error capturing TradingView chart: {e}")


# Load cookies from file
def load_cookies(driver, filepath):
    try:
        with open(filepath, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie {cookie}: {e}")
        print("Cookies loaded successfully.")
    except Exception as e:
        print(f"Error loading cookies: {e}")


# Function to post the screenshot and ask a question to OpenAI ChatGPT
def post_chart_to_openai_chat(driver, file_path: str, question: str):
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
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="__next"]/div[1]/div[2]/main/div[1]/div[2]/div[1]/div/form/div/div[2]/div/div/button'))
        )
        submit_button.click()

        # Wait for the specified element to appear, indicating the end of the response
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH,
                                            '/html/body/div[1]/div[1]/div[2]/main/div[1]/div[1]/div/div/div/div/div[3]/div/div/div[2]/div/div[2]'))
        )

        # Take a screenshot of the entire screen
        screen_screenshot = driver.get_screenshot_as_png()
        with open("response_element_screenshot.png", "wb") as file:
            file.write(screen_screenshot)
        print("Screenshot of the entire screen saved as 'response_element_screenshot.png'")

        # Wait for the response to appear
        response_element = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.XPATH, '/html/body/div[1]/div[1]/div[2]/main/div[1]/div[1]/div/div/div/div/div[3]/div/div/div[2]')
            )
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
                response_element = driver.find_element(By.XPATH,
                                                       '/html/body/div[1]/div[1]/div[2]/main/div[1]/div[1]/div/div/div/div/div[3]/div/div/div[2]')
            time.sleep(1)  # Wait for 1 second before checking again

        # Retrieve the response text correctly
        print("Response from OpenAI Chat:", response_text)
        return response_text, screen_screenshot

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
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None


def format_chart_analysis(chart_analysis):
    # Define regex patterns to match the required sections
    pattern_entry = r"(Entry.*)"

    # Search for the patterns in the chart analysis text
    match_entry = re.search(pattern_entry, chart_analysis, re.IGNORECASE | re.DOTALL)

    # Extract and return everything from the matched text downwards
    if match_entry:
        start_index = match_entry.start()
        return chart_analysis[start_index:].strip()
    else:
        return chart_analysis


# Send analysis results via Telegram
async def send_to_telegram(message: str, image_path: str, symbol: str, timeframe: str):
    try:
        intro = f"AI analysis for {symbol} on {timeframe}  :- "
        with open(image_path, 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo, caption=intro + message)
        print("Analysis sent to Telegram successfully.")
    except TelegramError as e:
        print(f"Error sending message to Telegram: {e}")


def main(symbol, timeframe):
    tradingview_chart_url = get_tradingview_chart_url(symbol, timeframe)

    # Step 1: Capture TradingView chart
    mozilla_screenshot_path = "mozilla_tradingview_chart.png"
    capture_tradingview_chart(tradingview_chart_url, mozilla_screenshot_path)

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

    # Step 2: Post the screenshot and ask a question to OpenAI ChatGPT
    question = """Analyze the following chart and predict the trend, entry points, exit points, and stop loss based on the trend.
    Can you share the output as per your analysis? Provide output in the format below.
    <Coin name from chart>
    Entry: <range1> - <range2>
    Leverage: Cross 20X
    Target 1:
    Target 2:
    Target 3:
    Stop Loss: """
    chart_analysis, screen_screenshot = post_chart_to_openai_chat(driver, mozilla_screenshot_path, question)
    # print(chart_analysis)

    formatted_analysis = format_chart_analysis(chart_analysis)
    print(formatted_analysis)

    # Step 3: Send analysis to Telegram
    if chart_analysis and mozilla_screenshot_path:
        asyncio.run(send_to_telegram(formatted_analysis, mozilla_screenshot_path, symbol, timeframe))


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    symbol = data.get("symbol", "BTCUSDT")
    timeframe = data.get("timeframe", "60")

    # Trigger the main function
    main(symbol, timeframe)

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(port=5000)
