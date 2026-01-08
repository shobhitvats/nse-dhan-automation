import time
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
REFRESH_INTERVAL = 120  # seconds
TOTAL_WINDOWS = 20
GRID_ROWS = 4
GRID_COLS = 5

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NSEFetcher:
    def __init__(self):
        self.url = "https://www.nseindia.com/market-data/most-active-equities"
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        self.driver = None

    def start(self):
        logging.info("Starting NSE Fetcher (Headless Browser)...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)

    def stop(self):
        if self.driver:
            self.driver.quit()

    def get_top_symbols(self, limit=20):
        try:
            self.driver.get(self.url)
            time.sleep(3) # Wait for initial load
            
            # Explicitly click the "Volume Spurts" tab
            try:
                # The tab usually has text "Volume Spurts"
                # Using XPath to find it robustly
                logging.info("Clicking 'Volume Spurts' tab...")
                tab = self.driver.find_element("xpath", "//*[contains(text(), 'Volume Spurts')]")
                tab.click()
                time.sleep(2) # Wait for table reload
            except Exception as e:
                logging.warning(f"Could not click 'Volume Spurts' tab: {e}")
                # Fallback to direct navigation if hash works, or just proceed (might be default tab)

            # Now scrape table
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            table = None
            
            # Find table with "Symbol" or "SYMBOL"
            for tbl in soup.find_all("table"):
                # Case insensitive check for Symbol
                if tbl.find("th", string=lambda x: x and "SYMBOL" in x.upper()):
                    table = tbl
                    break
            
            if not table:
                return self.get_fallback_symbols()
            
            symbols = []
            rows = table.find_all("tr")[1:] 
            for row in rows:
                cols = row.find_all("td")
                if cols and len(cols) > 0:
                    symbol = cols[0].get_text(strip=True).split()[0].strip()
                    # Filter out non-equity if needed. Volume Spurts usually are equities.
                    symbols.append(symbol)
                    if len(symbols) >= limit:
                        break
                        
            if not symbols: return self.get_fallback_symbols()
            return symbols

        except Exception as e:
            logging.error(f"Error fetching NSE: {e}")
            return self.get_fallback_symbols()

    def get_fallback_symbols(self):
        return ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LTIM", "LT", "AXISBANK", "HCLTECH", "ADANIENT", "MARUTI", "ASIANPAINT", "SUNPHARMA", "TITAN", "ULTRACEMCO", "TATASTEEL"]

class DhanGrid:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--start-maximized")
        self.driver = None

    def start(self):
        logging.info("Starting Dhan Grid Browser...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.options)
        self.driver.get("https://tv.dhan.co/")
        logging.info("Please log in to Dhan in the opened window.")

    def update_charts(self, symbols):
        logging.info(f"Updating dashboard with {len(symbols)} symbols...")
        
        # We need to construct a robust HTML/JS payload
        # 1. THE GRID LAYOUT & TABS
        # 2. THE LOGIC TO "TYPE" THE SYMBOL INTO EACH IFRAME (Since URL params fail)
        
        # JS to be injected into the main page
        # It handles:
        # A. Tab Switching
        # B. Waiting for IFrames to load
        # C. Injecting 'Typing' logic into frames
        
        main_script = """
        window.setupTabs = function() {
            window.showTab = function(index) {
                document.querySelectorAll('.grid-page').forEach(el => el.classList.remove('active-page'));
                document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
                document.getElementById('tab-' + index).classList.add('active-page');
                document.getElementById('btn-' + index).classList.add('active');
            };
        };
        
        window.injectSymbolLoader = function(iframeId, symbol) {
            let iframe = document.getElementById(iframeId);
            if(!iframe) return;
            
            iframe.onload = function() {
                console.log("Frame loaded: " + iframeId);
                // Wait for TradingView to fully init (e.g. 5-8 seconds)
                setTimeout(function() {
                    try {
                        let doc = iframe.contentWindow.document;
                        let win = iframe.contentWindow;
                        
                        console.log("Injecting symbol " + symbol + " into " + iframeId);
                        
                        // FIX: Explicitly click the Search Button first
                        // Common TV selectors:
                        // 1. global-header search (Dhan specific?)
                        // 2. [data-name="header-toolbar-symbol-search"] (Standard TV)
                        
                        let searchBtn = doc.querySelector('[data-name="header-toolbar-symbol-search"]') || 
                                        doc.querySelector('[class*="button-"] [class*="search-"]'); // Generic fallback
                        
                        if(searchBtn) {
                           console.log("Found search button, clicking...");
                           searchBtn.click();
                        } else {
                           // Try just typing on body (sometimes works if focused)
                           console.log("Search button not found, focusing body...");
                           win.focus();
                           doc.body.focus();
                        }
                        
                        setTimeout(function() {
                            // Now dispatch typing events
                            // Either into the popup input (if it appeared) or body
                            
                            let searchInput = doc.querySelector('input[data-role="search"]') || 
                                              doc.querySelector('input.search-input') ||
                                              doc.activeElement; // The popup usually focuses the input
                                              
                            if(searchInput && searchInput.tagName === 'INPUT') {
                                console.log("Typing into input field...");
                                searchInput.value = symbol;
                                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                                searchInput.dispatchEvent(new Event('change', { bubbles: true }));
                                
                                // Press Enter on the input
                                setTimeout(function() {
                                    searchInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                                }, 500);
                                
                            } else {
                                // Fallback: Simulate raw keystrokes on body
                                console.log("Typing on body...");
                                function typeString(str) {
                                    for(let i=0; i<str.length; i++) {
                                        let key = str[i];
                                        let code = key.charCodeAt(0);
                                        doc.body.dispatchEvent(new KeyboardEvent('keydown', { key: key, code: 'Key'+key.toUpperCase(), charCode: code, keyCode: code, which: code, bubbles: true }));
                                        doc.body.dispatchEvent(new KeyboardEvent('keypress', { key: key, code: 'Key'+key.toUpperCase(), charCode: code, keyCode: code, which: code, bubbles: true }));
                                        doc.body.dispatchEvent(new KeyboardEvent('keyup', { key: key, code: 'Key'+key.toUpperCase(), charCode: code, keyCode: code, which: code, bubbles: true }));
                                    }
                                }
                                typeString(symbol);
                                
                                setTimeout(function() {
                                     doc.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
                                }, 1500);
                            }
                            
                        }, 1000); // Wait for search box to open
                        
                    } catch(e) {
                         console.error("Injection failed for " + iframeId + ": " + e);
                    }
                }, 12000); // Increased wait time to 12s to ensure TV is ready
            };
        };
        """
        
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
        
        # Build HTML Structure
        html_content = '<div id="custom-ui" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:99999; background:#000;">'
        html_content += f'<style>{style}</style>'
        
        # Tabs
        html_content += '<div class="tab-bar">'
        for i in range(4):
            active = "active" if i == 0 else ""
            html_content += f'<button id="btn-{i}" class="tab-btn {active}" onclick="showTab({i})">PAGE {i+1}</button>'
        html_content += '</div>'
        
        # Pages
        chunks = [symbols[i:i + 6] for i in range(0, len(symbols), 6)]
        while len(chunks) < 4: chunks.append([])
        
        script_calls = ""
        
        for i in range(4):
            active_page = "active-page" if i == 0 else ""
            chunk = chunks[i]
            
            html_content += f'<div id="tab-{i}" class="grid-page {active_page}">'
            
            for slot_idx in range(6):
                if slot_idx < len(chunk):
                    s = chunk[slot_idx]
                    # We use unique ID to target this iframe for JS injection
                    fid = f"chart-frame-{i}-{slot_idx}"
                    # Base URL only
                    url = "https://tv.dhan.co/"
                    html_content += f'<iframe id="{fid}" src="{url}" allow="autoplay; encrypted-media"></iframe>'
                    
                    # Add JS call to inject symbol later
                    script_calls += f"injectSymbolLoader('{fid}', '{s}');\n"
                else:
                    html_content += '<div style="background:#111;"></div>' 
            
            html_content += '</div>'
            
        html_content += '</div>'
        
        # Execute Injection
        # We append the SCRIPT element properly to ensure it runs
        js_cmd = f"""
            // 1. Wipe Body
            document.body.innerHTML = `{html_content}`;
            
            // 2. Add Logic Script
            var s = document.createElement('script');
            s.textContent = `{main_script}`;
            document.head.appendChild(s);
            
            // 3. Init Tabs
            window.setupTabs();
            
            // 4. Hook up frames
            {script_calls}
        """
        
        self.driver.execute_script(js_cmd)

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
            symbols = fetcher.get_top_symbols(limit=20)
            if symbols:
                grid.update_charts(symbols)
            else:
                logging.warning("No symbols fetched.")
                
            logging.info(f"Sleeping for {REFRESH_INTERVAL} seconds...")
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        logging.info("Stopping...")
    finally:
        fetcher.stop()
        grid.close()

if __name__ == "__main__":
    main()
