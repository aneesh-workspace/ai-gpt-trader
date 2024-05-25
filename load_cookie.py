import pickle
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load cookies from file
def load_cookies(driver, filepath):
    try:
        with open(filepath, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
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

# Wait for ChatGPT to load and verify login
try:
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chat-container')]")))
    print("Logged in successfully.")
except Exception as e:
    print(f"Error verifying login: {e}")

# Your logic to interact with ChatGPT here

# Close the driver
driver.quit()
print("Driver quit.")
