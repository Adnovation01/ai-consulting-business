# ⚡ AI Consulting Engine: Nationwide Lead Hub

This folder is your complete, self-contained AI Consulting Business architecture. If you ever lose the AI chat, you can still operate the entire business manually using this folder and the commands below.

## Quick Start Commands

Just double-click the `.bat` files in this directory to run the different parts of the system:

### 1. The Command Center (The Dashboard)
To view your leads, filter by state, and mark leads for outreach:
* **Run:** Double-click `LAUNCH_CRM.bat`
* **What it does:** Starts a local web server and opens the beautiful dark-mode CRM dashboard in your browser. All data shown here is synced directly from your Master Excel sheet.

### 2. The Nationwide Scraper (Data Collection)
To scrape the entire country for brand new dental leads, run deep audits, and pull real emails from their websites:
* **Run:** Open PowerShell or Command Prompt in this folder and type: `python src/genuine_campaign.py`
* **What it does:** Uses headless browsers to stealthily navigate 50 states, extracts genuine verified emails, generates custom FOMO pain points, and automatically dumps them into `Dentist_Industry_Master.xlsx`.

### 3. The Master Database (Excel)
* **File:** `Dentist_Industry_Master.xlsx`
* **What it is:** This is the heart of the system. It contains 50 separate tabs (one for each state) plus a `CRM_SYNC` tab. 
* *Note: When you change an action to "SEND" in the Dashboard, the system will eventually tie to your email dispatcher to blast them directly from the `CRM_SYNC` tab.*

## File Overview
If you ever want to tweak the code yourself or have another AI look at it:
* `src/genuine_campaign.py`: The master script that controls Playwright to scrape the leads and emails.
* `src/lead_researcher.py`: Overviews the deep AI audit logic.
* `src/excel_manager.py`: Controls how leads are written into your Master Excel sheet.
* `dashboard/index.html`: The HTML file that creates your beautiful UI.
* `dashboard/crm_data.json`: The raw JSON feed that powers the visual dashboard.

**Requirements if setting up on a new PC:**
If you move this folder to a new computer, make sure you install python and run:
`pip install openpyxl pandas playwright requests bs4`
`playwright install`
