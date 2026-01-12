import time
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# --- Configuration ---
REFRESH_INTERVAL = 300  # seconds (5 minutes)
TOTAL_WINDOWS = 20
GRID_ROWS = 4
GRID_COLS = 5

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NSEFetcher:
    def __init__(self):
        self.url = "https://www.nseindia.com/market-data/volume-gainers-spurts"
        self.options = Options()
        # self.options.add_argument("--headless")  # DISABLED to avoid detection
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.driver = None

    def start(self):
        logging.info("Starting NSE Fetcher...")
        self.driver = webdriver.Chrome(options=self.options)

    def stop(self):
        if self.driver:
            self.driver.quit()

    def get_top_symbols(self, limit=20):
        # Retry loop for robustness
        for attempt in range(3):
            try:
                if attempt > 0:
                    logging.info(f"Retrying NSE fetch (Attempt {attempt+1}/3)...")
                    self.driver.refresh()
                    time.sleep(5) # Cooldown
                else:
                    self.driver.get(self.url)
                
                # Strict Wait: Wait for actual data rows, not just table tag
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
                )

                # Now scrape table
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                table = None
                
                # Find table with "Symbol" or "SYMBOL"
                for tbl in soup.find_all("table"):
                    if tbl.find("th", string=lambda x: x and "SYMBOL" in x.upper()):
                        table = tbl
                        break
                
                if not table:
                    raise Exception("Table with SYMBOL header not found")
                
                symbols = []
                rows = table.find_all("tr")[1:] 
                for row in rows:
                    cols = row.find_all("td")
                    if cols and len(cols) > 0:
                        symbol = cols[0].get_text(strip=True).split()[0].strip()
                        symbols.append(symbol)
                        if len(symbols) >= limit:
                            break
                            
                if not symbols: 
                     raise Exception("No symbols parsed from table")
                     
                logging.info(f"Successfully fetched {len(symbols)} symbols from NSE.")
                return symbols
    
            except Exception as e:
                logging.warning(f"Error fetching NSE (Attempt {attempt+1}): {e}")
                
        logging.error("Failed to fetch symbols after 3 attempts. NO FALLBACK DATA used.")
        return []

    # Fallback method removed as per user request


class DhanGrid:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--start-maximized")
        self.options.add_argument(f"user-data-dir={os.getcwd()}/user_data")
        
        # High-Performance Flags (Safe Subset)
        self.options.add_argument("--enable-gpu-rasterization")
        self.options.add_argument("--ignore-gpu-blocklist")
        self.options.add_argument("--disable-background-timer-throttling")
        
        self.options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        self.driver = None
        self.is_initialized = False

    def start(self):
        logging.info("Starting Dhan Grid Browser...")
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.get("https://tv.dhan.co/")
        logging.info("Please log in to Dhan in the opened window.")

    def init_grid(self, symbols):
        logging.info("Initializing Grid Layout with PRIORITY LOADING...")
        
        style = """
            body { margin: 0; overflow: hidden; background: #000; font-family: sans-serif; }
            .tab-bar { position: absolute; top: 0; left: 0; width: 100%; height: 35px; background: #222; display: flex; z-index: 100000; border-bottom: 2px solid #444; }
            .tab-btn { flex: 1; border: none; background: #333; color: #fff; cursor: pointer; border-right: 1px solid #444; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
            .tab-btn:hover { background: #444; }
            .tab-btn.active { background: #007bff; font-weight: bold; color: white; }
            .grid-page { display: none; width: 100vw; height: calc(100vh - 35px); margin-top: 35px; grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(2, 1fr); gap: 2px; background: #111; }
            .grid-page.active-page { display: grid; }
            iframe { width: 100%; height: 100%; border: none; background: #000; }
        """
        
        scripts = """
        // Helper to load a tab's iframes with STAGGERED delay
        window.loadTab = function(index) {
            let container = document.getElementById('tab-' + index);
            if(!container) return;
            let frames = container.querySelectorAll('iframe');
            frames.forEach((iframe, i) => {
                let pending = iframe.getAttribute('data-pending-src');
                if(pending) {
                    // Stagger load by 300ms per frame to prevent CPU choke
                    setTimeout(() => {
                        iframe.src = pending;
                        iframe.removeAttribute('data-pending-src');
                    }, i * 300);
                }
            });
        };

        window.showTab = function(index) {
            document.querySelectorAll('.grid-page').forEach(el => el.classList.remove('active-page'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + index).classList.add('active-page');
            document.getElementById('btn-' + index).classList.add('active');
            
            // On-Demand Load (Staggered)
            window.loadTab(index);
        };

        // Smart Update: Handles both loaded and pending frames
        window.updateChart = function(id, symbol) {
            let el = document.getElementById(id);
            if(el) {
                let newSrc = "https://tv.dhan.co/?symbol=NSE:" + symbol;
                
                if (el.hasAttribute('data-pending-src')) {
                    el.setAttribute('data-pending-src', newSrc);
                    el.setAttribute('data-symbol', symbol);
                } 
                else if(el.getAttribute('data-symbol') !== symbol) {
                    el.src = newSrc;
                    el.setAttribute('data-symbol', symbol);
                }
            }
        };
        
        // Trigger load for hidden pages only (Page 1 is already loaded)
        window.loadTab(0); // Ensures any pending frames on Page 1 are caught, though there shouldn't be any
        """
        
        html_content = '<div id="custom-ui" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:99999; background:#000;">'
        html_content += f'<style>{style}</style>'
        html_content += '<link rel="preconnect" href="https://tv.dhan.co">'
        html_content += f'<script>{scripts}</script>'
        
        # Tabs
        html_content += '<div class="tab-bar">'
        for i in range(4):
            active = "active" if i == 0 else ""
            html_content += f'<button id="btn-{i}" class="tab-btn {active}" onclick="showTab({i})">PAGE {i+1}</button>'
        html_content += '</div>'
        
        # Structure for 4 pages x 6 charts
        chunks = [symbols[i:i + 6] for i in range(0, len(symbols), 6)]
        while len(chunks) < 4: chunks.append([])

        for i in range(4):
            active_page = "active-page" if i == 0 else ""
            html_content += f'<div id="tab-{i}" class="grid-page {active_page}">'
            chunk = chunks[i]
            for slot_idx in range(6):
                fid = f"chart-frame-{i}-{slot_idx}"
                if slot_idx < len(chunk):
                    # Use generic NIFTY URL to guarantee Toolbar/Search Button loads
                    src = "https://tv.dhan.co/?symbol=NSE:NIFTY" 
                    
                    if i == 0:
                        # Page 1: Direct Injection (0ms Latency - Critical Path)
                        html_content += f'<iframe id="{fid}" src="{src}" allow="autoplay; encrypted-media"></iframe>'
                    else:
                        # Page 2-4: DEFER (Pending/Staggered)
                        html_content += f'<iframe id="{fid}" src="about:blank" data-pending-src="{src}" allow="autoplay; encrypted-media"></iframe>'
                else:
                    html_content += f'<iframe id="{fid}" src="about:blank" allow="autoplay; encrypted-media"></iframe>'
            html_content += '</div>'
        html_content += '</div>'
        
        # NUCLEAR OPTION: Use document.write() to completely replace the page content.
        # This prevents any React/SPA re-hydration from overwriting our grid.
        js_cmd = f"document.open(); document.write(`{html_content}`); document.close();"
        self.driver.execute_script(js_cmd)
        
        # We don't need to re-inject 'scripts' because document.write executes <script> tags inline.
        self.is_initialized = True
        logging.info("Grid Initialized (Staggered Loading Active).")

        self.is_initialized = True
        logging.info("Grid Initialized (Staggered Loading Active).")

    def cleanup_ui(self):
        """
        Injects CSS into each chart frame to hide the Top Toolbar (Header),
        giving a clean 'Chart-Only' view and removing 'Sell/Buy' buttons.
        """
        logging.info("Cleaning up UI (Hiding Toolbars)...")
        # CSS to hide Top Header, Left Toolbar, and maximize chart area
        css_hide = """
            .layout__area--top, 
            .header-chart-panel, 
            .tv-header,
            .chart-toolbar,
            [data-role='toolbar'],
            .drawing-toolbar,
            .layout__area--left { 
                display: none !important; 
            }
        """
        
        # We need to switch to each frame to inject this
        # We process Page 1 (Visible) immediately. Pages 2-4 can happen in background?
        # Actually, Selenium can switch to hidden frames too.
        
        for i in range(4):
            for slot_idx in range(6):
                fid = f"chart-frame-{i}-{slot_idx}"
                try:
                    frame = self.driver.find_element(By.ID, fid)
                    self.driver.switch_to.frame(frame)
                    
                    # Inject Style
                    js = f"var s=document.createElement('style'); s.innerHTML=`{css_hide}`; document.head.appendChild(s);"
                    self.driver.execute_script(js)
                    
                    self.driver.switch_to.default_content()
                except Exception:
                    # Frame might be loading or failed, skip silently
                    self.driver.switch_to.default_content()
                    pass
        logging.info("UI Cleanup Complete.")

    def update_charts(self, symbols):
        logging.info(f"Updating dashboard with {len(symbols)} symbols via SEARCH & TYPE...")
        
        if not self.is_initialized:
            self.init_grid(symbols)
            # Give frames a moment to load - Reduced to 0.5s for MAX speed
            logging.info("Waiting 0.5s for Grid to stabilize...")
            time.sleep(0.5) 
        
        # We need to iterate through frames and type the symbol
        # Map symbols to frames same as init
        chunks = [symbols[i:i + 6] for i in range(0, len(symbols), 6)]
        while len(chunks) < 4: chunks.append([])
        
        for i in range(4): # For each page
            chunk = chunks[i]
            if len(chunk) == 0: continue
            
            # Switch Tabs for visibility (Required for Selenium interaction)
            try:
                logging.info(f"Switching to PAGE {i+1}...")
                tab_btn = self.driver.find_element(By.ID, f"btn-{i}")
                tab_btn.click()
                tab_btn.click()
                time.sleep(0.5) # Fast transition wait
            except Exception as e:
                logging.error(f"Failed to switch to Page {i+1}: {e}")
                continue

            for slot_idx in range(6):
                if slot_idx >= len(chunk): break
                
                raw_symbol = chunk[slot_idx]
                # LOWERCASE CONVERSION (User Request: Prevent Shift+Keys)
                symbol = raw_symbol.lower() # 'SBIN' -> 'sbin'
                
                fid = f"chart-frame-{i}-{slot_idx}"
                
                try:
                    # switch to frame
                    frame = self.driver.find_element(By.ID, fid)
                    self.driver.switch_to.frame(frame)
                    
                    # 1. HOTKEY KILLER INJECTION
                    hk_killer = """
                        window.addEventListener('keydown', function(e) {
                            // Allow typing in INPUT fields
                            if(e.target.tagName === 'INPUT') return;
                            
                            // Block Dangerous Instant Orders: Shift + S (Sell), Shift + B (Buy)
                            // We allow plain 's' and 'b' so the user can Type-to-Search (e.g. 'SBIN')
                            var key = e.key.toLowerCase();
                            if(e.shiftKey && (key === 's' || key === 'b')) {
                                e.stopImmediatePropagation();
                                e.preventDefault();
                                console.log('Blocked dangerous key: Shift + ' + key);
                            }
                            // Block Fullscreen 'f'
                            if(key === 'f') {
                                e.stopImmediatePropagation();
                                e.preventDefault();
                            }
                        }, true);
                    """
                    self.driver.execute_script(hk_killer)
                    
                    # -------------------------------------------------------------
                    # PRIMARY STRATEGY: TYPE-TO-SEARCH (NATIVE)
                    # -------------------------------------------------------------
                    # As requested, this is now the FIRST and ONLY priority.
                    # It bypasses UI detection issues and is the fastest method.
                    try:
                        # 1. Focus Canvas (ensure keystrokes register)
                        canvases = self.driver.find_elements(By.TAG_NAME, "canvas")
                        if canvases:
                            canvases[0].click()
                        else:
                            self.driver.find_element(By.TAG_NAME, "body").click()
                        time.sleep(0.5)

                        # 2. Type AND Enter in one continuous chain
                        # Sequence: Type Symbol -> Wait 0.35s -> Arrow Down -> Enter
                        actions = ActionChains(self.driver)
                        actions.send_keys(symbol)
                        actions.pause(0.35) # Validated minimum wait for network
                        actions.send_keys(Keys.ENTER)
                        actions.perform()
                        
                        # 3. Success (No validation wait needed, assume success)
                        logging.info(f"Updated {fid} -> {symbol}")
                        
                    except Exception as e:
                        logging.error(f"Failed update {fid}: {e}")

                except Exception as e:
                    logging.error(f"Frame access error {fid}: {e}")
                finally:
                    self.driver.switch_to.default_content()
        
        # Cleanup UI AFTER all typing is done
        self.cleanup_ui()
        logging.info("Finished Search & Type updates.")


    def check_console(self):
        if not self.driver: return
        try:
            logs = self.driver.get_log('browser')
            for entry in logs:
                msg = entry['message']
                if "SEVERE" in str(entry['level']):
                    logging.info(f"JS CONSOLE: {msg}")
        except Exception:
            pass

    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    fetcher = NSEFetcher()
    grid = DhanGrid()
    
    try:
        fetcher.start()
        grid.start()
        
        print("")
        print(">>> ------------------------------------------------ <<<")
        print(">>> PLEASE LOG IN TO DHAN IN THE NEW CHROME WINDOW <<<")
        print(">>> ------------------------------------------------ <<<")
        print("")
        input("Press Enter here AFTER you are fully logged in and see the chart...")
        
        while True:
            # Fetch 30
            symbols = fetcher.get_top_symbols(limit=30)
            
            if symbols:
                if len(symbols) > 1:
                    symbols = symbols[1:25]
                grid.update_charts(symbols)
            else:
                logging.warning("No symbols fetched.")
                
            logging.info(f"Sleeping for {REFRESH_INTERVAL} seconds...")
            # Sleep loop
            for _ in range(30):
                time.sleep(1)
                # verify browser is still open
                try:
                    grid.driver.title
                except:
                    logging.error("Browser closed.")
                    return
            
            time.sleep(REFRESH_INTERVAL - 30)
            
    except KeyboardInterrupt:
        logging.info("Stopping...")
    except Exception as e:
         logging.error(f"Critical Error: {e}")
    finally:
        fetcher.stop()
        grid.close()

if __name__ == "__main__":
    main()
