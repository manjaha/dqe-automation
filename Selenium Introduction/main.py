import time
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = webdriver.Chrome(options=options)
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
        
        print(f"   Found headers: {headers}")
        
        # Locator 3: Find ALL text elements with class 'cell-text'
        all_texts = table_container.find_elements(By.CSS_SELECTOR, "text.cell-text")
        
        # Extract text, skipping headers
        all_data = []
        for text_elem in all_texts:
            text = text_elem.text.strip()
            if text and text not in headers:
                all_data.append(text)
        
        print(f"   Total cell-text elements found: {len(all_texts)}")
        print(f"   Data cells (excluding headers): {len(all_data)}")
        
        # Organize into rows (3 columns)
        num_columns = len(headers)
        rows = []
        
        if num_columns > 0:
            for i in range(0, len(all_data), num_columns):
                row = all_data[i:i + num_columns]
                if len(row) == num_columns:
                    rows.append(row)
        
        print(f"   Organized into {len(rows)} rows")
        
        if headers and rows:
            df = pd.DataFrame(rows, columns=headers)
            df.to_csv(output_file, index=False)
            print(f"✅ Table saved: {len(df)} rows, {len(headers)} columns")
        else:
            print(f"⚠️ Could not create table (headers: {len(headers)}, rows: {len(rows)})")
            # Create empty file so deliverable exists
            pd.DataFrame(columns=headers if headers else ["Column1", "Column2", "Column3"]).to_csv(output_file, index=False)
            
    except TimeoutException:
        print("❌ Timeout: Table not found")
    except Exception as e:
        print(f"❌ Error extracting table: {e}")
        import traceback
        traceback.print_exc()


def extract_doughnut_data(driver: WebDriver, output_file):
    """
    Extract doughnut chart data from Plotly pie chart
    """
    try:
        # Find all pie slices
        slices = driver.find_elements(By.CSS_SELECTOR, "g.slice")
        
        data = []
        for slice_elem in slices:
            try:
                # Extract text from each slice
                text_elem = slice_elem.find_element(By.CSS_SELECTOR, "text.slicetext")
                text_content = text_elem.get_attribute("data-unformatted")
                
                if text_content:
                    # Parse "Clinic<br>33.33" format
                    parts = text_content.replace("<br>", "|").split("|")
                    if len(parts) >= 2:
                        facility_type = parts[0].strip()
                        value = parts[1].strip()
                        data.append([facility_type, value])
            except Exception as e:
                continue
        
        if data:
            df = pd.DataFrame(data, columns=["Facility Type", "Min Average Time Spent"])
            df.to_csv(output_file, index=False)
            print(f"✅ Chart data saved to {output_file} ({len(data)} entries)")
        else:
            print(f"⚠️ No chart data found for {output_file}")
            pd.DataFrame(columns=["Facility Type", "Min Average Time Spent"]).to_csv(output_file, index=False)
        
    except Exception as e:
        print(f"⚠️ Error extracting chart data: {e}")


def process_doughnut_chart(driver: WebDriver):
    """
    Iterate through doughnut chart legend items and capture screenshots
    """
    print("🍩 Processing doughnut chart...")
    
    try:
        time.sleep(2)
        
        # Screenshot 0: Initial state
        driver.save_screenshot("screenshot0.png")
        extract_doughnut_data(driver, "doughnut0.csv")
        print("✅ screenshot0.png saved")
        
        # Find legend groups (the parent containers)
        legend_groups = driver.find_elements(By.CSS_SELECTOR, "g.legend g.groups g.traces")
        
        print(f"Found {len(legend_groups)} legend group(s)")
        
        screenshot_num = 1
        
        for i, group in enumerate(legend_groups):
            try:
                # Move to element and click
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(driver)
                actions.move_to_element(group).click().perform()
                time.sleep(1)
                
                # Take screenshot
                driver.save_screenshot(f"screenshot{screenshot_num}.png")
                extract_doughnut_data(driver, f"doughnut{screenshot_num}.csv")
                print(f"✅ screenshot{screenshot_num}.png saved")
                
                screenshot_num += 1
                
            except Exception as e:
                print(f"⚠️ Error processing group {i}: {e}")
                continue
        
        # Edge case: Toggle all back
        try:
            for group in legend_groups:
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(group).click().perform()
                    time.sleep(0.3)
                except:
                    pass
            
            driver.save_screenshot(f"screenshot{screenshot_num}.png")
            extract_doughnut_data(driver, f"doughnut{screenshot_num}.csv")
            print(f"✅ screenshot{screenshot_num}.png (all filters toggled)")
        except Exception as e:
            print(f"⚠️ Edge case handling: {e}")
                
    except Exception as e:
        print(f"❌ Error in doughnut chart processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Get absolute path to report
    report_path = Path("report.html").absolute()
    
    if not report_path.exists():
        print(f"❌ Report not found at: {report_path}")
        print("Please run: podman cp jenkins:/generated_report/report.html .")
        exit(1)
    
    file_url = report_path.as_uri()
    print(f"📄 Opening report: {file_url}\n")
    
    with SeleniumWebDriverContextManager() as driver:
        # Load the HTML report
        driver.get(file_url)
        print("✅ Report loaded\n")
        
        # Give page time to fully render Plotly charts
        time.sleep(3)
        
        # Task 1: Extract table
        extract_table_to_csv(driver)
        print()
        
        # Task 2: Process doughnut chart
        process_doughnut_chart(driver)
        print()
        
        print("🎉 Automation complete!")
        
        # Keep browser open for inspection
        print("Browser will close in 10 seconds...")
        time.sleep(10)