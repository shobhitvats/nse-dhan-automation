#!/bin/bash
# Install Python dependencies locally
echo "Installing dependencies..."
pip install --user -r requirements.txt || python3 -m pip install --user -r requirements.txt

# Post-install check
if python3 -c "import selenium; import bs4; import requests" 2>/dev/null; then
    echo "Dependencies installed successfully!"
else
    echo "Dependency installation failed. Please install 'selenium', 'requests', 'beautifulsoup4', 'webdriver-manager' manually."
fi
