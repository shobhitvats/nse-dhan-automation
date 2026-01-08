# NSE-Dhan Automation Setup

## Prerequisites
1.  **Google Chrome** must be installed.
2.  **Python 3** must be installed.

## Setup
1.  Open a terminal in this folder.
2.  Run the setup script to install dependencies:
    ```bash
    ./setup.sh
    ```
    (Or manually install: `pip install selenium requests beautifulsoup4 webdriver-manager`)

## Quick Start

1.  **Open Terminal**
2.  **Navigate to the folder**:
    ```bash
    cd /home/ratul/Desktop/MFT/nse_dhan_automation
    ```
3.  **Run the Script**:
    ```bash
    python3 main.py
    ```
4.  **Follow On-Screen Instructions**:
    - A Chrome window will open.
    - **Log in to Dhan** in that window.
    - Come back to your terminal and **press Enter**.
    - The grid will appear.

## Troubleshooting
-   **Window Size**: If windows are too small or overlap, adjust `SCREEN_WIDTH` and `SCREEN_HEIGHT` in `main.py`.
-   **URL Issues**: If charts don't load the specific symbol, Dhan might have changed their URL structure. The script uses `https://tv.dhan.co/?symbol={SYMBOL}`.
