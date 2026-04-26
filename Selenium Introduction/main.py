import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pathlib import Path


class SeleniumWebDriverContextManager:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
    
    def __enter__(self) -> WebDriver:
        """Initialize and return WebDriver"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        
        return self.driver
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up WebDriver"""
        if self.driver:
            self.driver.quit()
        return False


def extract_table_to_csv(driver: WebDriver, output_file="table.csv"):
    """
    Extract Plotly table content using multiple locator types
    """
    print(f"📊 Extracting table to {output_file}...")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Locator 1: By CLASS_NAME
        table_container = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "table"))
        )
        
        # Locator 2: By CSS_SELECTOR - get headers
        header_elements = table_container.find_elements(By.CSS_SELECTOR, "g#header text.cell-text")
        headers = [h.text.strip() for h in header_elements if h.text.strip()]
        
        # Locator 3: By CSS_SELECTOR - get all data cells
        all_texts = table_container.find_elements(By.CSS_SELECTOR, "text.cell-text")
        
        # Extract data, skipping headers
        all_data = [text.text.strip() for text in all_texts 
                    if text.text.strip() and text.text.strip() not in headers]
        
        # Organize into rows
        num_columns = len(headers)
        rows = [all_data[i:i + num_columns] for i in range(0, len(all_data), num_columns)
                if len(all_data[i:i + num_columns]) == num_columns]
        
        if headers and rows:
            df = pd.DataFrame(rows, columns=headers)
            df.to_csv(output_file, index=False)
            print(f"✅ Table saved: {len(df)} rows, {len(headers)} columns")
        else:
            pd.DataFrame(columns=headers).to_csv(output_file, index=False)
            
    except TimeoutException:
        print("❌ Timeout: Table not found")
    except Exception as e:
        print(f"❌ Error extracting table: {e}")


def extract_doughnut_data(driver: WebDriver, output_file):
    """
    Extract doughnut chart data from Plotly pie chart
    """
    try:
        slices = driver.find_elements(By.CSS_SELECTOR, "g.slice")
        
        data = []
        for slice_elem in slices:
            try:
                text_elem = slice_elem.find_element(By.CSS_SELECTOR, "text.slicetext")
                text_content = text_elem.get_attribute("data-unformatted")
                
                if text_content:
                    parts = text_content.replace("<br>", "|").split("|")
                    if len(parts) >= 2:
                        data.append([parts[0].strip(), parts[1].strip()])
            except:
                continue
        
        df = pd.DataFrame(data, columns=["Facility Type", "Min Average Time Spent"]) if data else pd.DataFrame(columns=["Facility Type", "Min Average Time Spent"])
        df.to_csv(output_file, index=False)
        
        if data:
            print(f"✅ Chart data saved to {output_file} ({len(data)} entries)")
        else:
            print(f"⚠️ No chart data found for {output_file}")
        
    except Exception as e:
        print(f"⚠️ Error extracting chart data: {e}")


def process_doughnut_chart(driver: WebDriver):
    """
    Iterate through doughnut chart legend items and capture screenshots
    """
    print("🍩 Processing doughnut chart...")
    
    try:
        time.sleep(2)  # Wait for chart to render
        
        # Screenshot 0: Initial state
        driver.save_screenshot("screenshot0.png")
        extract_doughnut_data(driver, "doughnut0.csv")
        print("✅ screenshot0.png saved")
        
        # Find legend groups
        legend_groups = driver.find_elements(By.CSS_SELECTOR, "g.legend g.groups g.traces")
        print(f"Found {len(legend_groups)} legend group(s)")
        
        screenshot_num = 1
        
        # Click each legend item
        for i, group in enumerate(legend_groups):
            try:
                ActionChains(driver).move_to_element(group).click().perform()
                time.sleep(1)
                
                driver.save_screenshot(f"screenshot{screenshot_num}.png")
                extract_doughnut_data(driver, f"doughnut{screenshot_num}.csv")
                print(f"✅ screenshot{screenshot_num}.png saved")
                
                screenshot_num += 1
                
            except Exception as e:
                print(f"⚠️ Error processing group {i}: {e}")
                continue
        
        # Edge case: Toggle all back
        for group in legend_groups:
            try:
                ActionChains(driver).move_to_element(group).click().perform()
                time.sleep(0.3)
            except:
                pass
        
        driver.save_screenshot(f"screenshot{screenshot_num}.png")
        extract_doughnut_data(driver, f"doughnut{screenshot_num}.csv")
        print(f"✅ screenshot{screenshot_num}.png (all filters toggled)")
                
    except Exception as e:
        print(f"❌ Error in doughnut chart processing: {e}")


if __name__ == "__main__":
    report_path = Path("report.html").absolute()
    
    if not report_path.exists():
        print(f"❌ Report not found at: {report_path}")
        print("💡 Copy report.html to this directory first")
        exit(1)
    
    print(f"📄 Opening report: {report_path.as_uri()}\n")
    
    with SeleniumWebDriverContextManager(headless=True) as driver:
        driver.get(report_path.as_uri())
        print("✅ Report loaded\n")
        
        time.sleep(3)  # Wait for Plotly charts to render
        
        extract_table_to_csv(driver)
        print()
        
        process_doughnut_chart(driver)
        print()
        
        print("🎉 Automation complete!")