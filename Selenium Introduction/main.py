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
        # Wait for table visible
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "table")))
        
        # LOCATOR 1: By.CLASS_NAME - Get table root
        table = driver.find_element(By.CLASS_NAME, "table")
        
        # LOCATOR 2: By.CLASS_NAME - Get all columns  
        columns = table.find_elements(By.CLASS_NAME, "y-column")
        
        headers = []
        all_data = []
        
        for column in columns:
            # LOCATOR 3: By.ID - Get column header
            header = column.find_element(By.ID, "header").text.strip()
            headers.append(header)
            
            # Get parent cell elements (which have position info)
            parent_cells = column.find_elements(By.CSS_SELECTOR, "g.column-cell")
            
            # Extract cells with their Y positions
            cells_with_position = []
            for parent in parent_cells:
                transform = parent.get_attribute("transform")
                if "translate" in transform:
                    # Extract Y coordinate
                    y_str = transform.split(",")[1].replace(")", "").strip()
                    y_pos = float(y_str)
                    
                    # LOCATOR 4: By.CLASS_NAME - Get text from cell
                    try:
                        text_elem = parent.find_element(By.CLASS_NAME, "cell-text")
                        text = text_elem.text.strip()
                        
                        # Filter out header
                        if text and text != header:
                            cells_with_position.append((y_pos, text))
                    except:
                        pass
            
            # Sort by Y position (visual order)
            cells_with_position.sort(key=lambda x: x[0])
            
            # Extract just the text values
            column_data = [text for y, text in cells_with_position]
            all_data.append(column_data)
        
        print(f"   Headers: {headers}")
        print(f"   Rows extracted: {len(all_data[0])}")
        
        # Transpose columns to rows
        num_rows = len(all_data[0])
        rows = [[all_data[col][i] for col in range(len(all_data))] 
                for i in range(num_rows)]
        
        df = pd.DataFrame(rows, columns=headers)
        df.to_csv(output_file, index=False)
        print(f"✅ Table saved: {len(df)} rows")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def extract_doughnut_data(driver: WebDriver, output_file):
    """
    Extract doughnut chart data from Plotly pie chart
    """
    try:
        # Wait for chart layer
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pielayer")))
        
        # Get chart root
        doughnut = driver.find_element(By.CLASS_NAME, "pielayer")
        
        # Get slice labels (data-notex='1' = real labels only)
        slice_labels = doughnut.find_elements(By.CSS_SELECTOR, "text.slicetext[data-notex='1']")
        
        data = []
        for label in slice_labels:
            try:
                # Get lines in each label: tspans[0] = category, tspans[1] = value
                tspans = label.find_elements(By.TAG_NAME, "tspan")
                
                if len(tspans) >= 2:
                    category = tspans[0].text.strip()
                    value = tspans[1].text.strip()
                    data.append([category, value])
            except:
                continue
        
        if data:
            df = pd.DataFrame(data, columns=["Facility Type", "Min Average Time Spent"])
            df.to_csv(output_file, index=False)
            print(f"✅ Chart data saved to {output_file} ({len(data)} entries)")
        else:
            # No data (all slices hidden)
            df = pd.DataFrame(columns=["Facility Type", "Min Average Time Spent"])
            df.to_csv(output_file, index=False)
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