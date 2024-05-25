import pickle
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

# Navigate to Google login page
print("Navigating to Google login page...")
try:
    driver.get("https://chat.openai.com/")
    print("Page loaded successfully.")
except Exception as e:
    print(f"Error loading page: {e}")
    driver.quit()
    raise

# Wait for manual login
input("Log in manually and press Enter...")

# Save cookies to a file
print("Saving cookies...")
try:
    with open("cookies.pkl", "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("Cookies saved successfully.")
except Exception as e:
    print(f"Error saving cookies: {e}")
finally:
    driver.quit()
    print("Driver quit.")
