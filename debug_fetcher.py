from main import NSEFetcher
import logging
import sys

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def test_fetcher():
    fetcher = NSEFetcher()
    try:
        fetcher.start()
        print("Fetching symbols...")
        symbols = fetcher.get_top_symbols(limit=30)
        print(f"Total Symbols Fetched: {len(symbols)}")
        print(f"Symbols: {symbols}")
        
        # logical verify
        if len(symbols) == 20 and symbols[0] == "RELIANCE":
             print("DIAGNOSIS: Fetcher is using FALLBACK list.")
        else:
             print("DIAGNOSIS: Fetcher is working (real data).")
             
    except Exception as e:
        print(f"Error: {e}")
    finally:
        fetcher.stop()

if __name__ == "__main__":
    test_fetcher()
