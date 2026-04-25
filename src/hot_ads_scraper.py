"""
Hot Ads Scraper - Targeted High-Intent Lead Acquisition
Spoofs GPS location to bypass geographical limitations and extracts ONLY businesses actively paying for Google Ads.
"""
import os, json, time, re, random
import subprocess
import sys
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup

# ==========================================
# ⚙️ HOT ADS CONFIGURATION ⚙️
# ==========================================
INDUSTRY_TARGET = "roofing contractor" 

# We will spoof the browser's exact GPS location to trick Google into showing local ads for these cities!
TARGET_CITIES = [
    # city name, state, latitude, longitude
    ("Dallas", "TX", 32.7767, -96.7970),
    ("Miami", "FL", 25.7617, -80.1918),
    ("Atlanta", "GA", 33.7490, -84.3880)
]

def search_for_email(url):
    """Deep crawl the business website to extract their real email"""
    try:
        response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, response.text)
            valid = [e for e in set(emails) if not any(x in e.lower() for x in ['wix', 'png', 'jpg', 'sentry', 'example', 'test'])]
            
            if not valid:
                soup = BeautifulSoup(response.text, 'html.parser')
                contact_links = [a.get('href') for a in soup.find_all('a', href=True) if 'contact' in a.get('href', '').lower()]
                if contact_links:
                    contact_url = contact_links[0]
                    if not contact_url.startswith('http'):
                        contact_url = url.rstrip('/') + '/' + contact_url.lstrip('/')
                    try:
                        res2 = requests.get(contact_url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                        emails2 = re.findall(email_pattern, res2.text)
                        valid = [e for e in set(emails2) if not any(x in e.lower() for x in ['wix', 'png', 'jpg', 'sentry'])]
                    except: pass
            return valid[0] if valid else None
    except: return None
    return None

def scrape_hot_ads():
    print("🔥 BOOTING HOT ADS SCRAPER - HIGH INTENT BUYERS 🔥")
    print(f"Targeting: {INDUSTRY_TARGET}")
    leads = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for city, state, lat, lon in TARGET_CITIES:
            print(f"\n[SPOOFING GPS] Teleporting connection to {city}, {state}...")
            
            # 1. Create a brand new context pretending to be physically standing in that city.
            context = browser.new_context(
                geolocation={"latitude": lat, "longitude": lon},
                permissions=["geolocation"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            query = f"{INDUSTRY_TARGET} {city} {state}".replace(" ", "+")
            url = f"https://www.google.com/search?q={query}&gl=us&hl=en"
            
            try:
                page.goto(url, wait_until="networkidle", timeout=15000)
                time.sleep(2) # let ads load
                
                # Google changes its Ad selectors often, these capture top & bottom sponsored blocks
                ad_elements = page.query_selector_all('div[data-text-ad="1"]')
                print(f"Found {len(ad_elements)} businesses actively PAYING for clicks right now.")
                
                for ad in ad_elements:
                    # Look for the hidden tracking URL or displayed link
                    link_el = ad.query_selector('a')
                    name_el = ad.query_selector('div[role="heading"]')
                    
                    if link_el and name_el:
                        ad_url = link_el.get_attribute("href")
                        business_name = name_el.inner_text().strip()
                        
                        # Google uses tracking proxies like https://www.google.com/aclk?....
                        # We must 'click' or extract the real domain. 
                        # To be lightweight, we can regex the visible url text.
                        visible_url_el = ad.query_selector('span:has-text(".com")')
                        real_domain = ""
                        if visible_url_el:
                            real_domain = visible_url_el.inner_text().split(" ")[0]
                        else:
                            real_domain = ad_url # fallback
                            
                        # If we have a domain format (e.g. www.roofing.com)
                        if ".com" in real_domain or ".net" in real_domain or ".org" in real_domain:
                            if not real_domain.startswith("http"):
                                real_domain = "https://" + real_domain
                                
                            print(f"  -> Intercepted Ad: {business_name}")
                            email = search_for_email(real_domain)
                            
                            if email:
                                print(f"     [+] Verified target email: {email}")
                                leads.append({
                                    "name": business_name,
                                    "url": real_domain,
                                    "email": email,
                                    "location": f"{city}, {state}",
                                    "niche": INDUSTRY_TARGET.capitalize(),
                                    "analysis": {
                                        "hard_pain_points": [
                                            f"You are actively paying Google $10-$40 per click, but your site has friction points preventing conversions.",
                                            "Your competitors are shifting away from Google Ads into AI-automated inbound."
                                        ],
                                        "estimated_revenue_leak": "High Cost-Per-Acquisition (CPA)",
                                        "market_gap_analysis": f"You are bidding on expensive '{city}' keywords while generating shared leads instead of exclusive ones.",
                                        "conversion_friction": "Traffic from expensive ad clicks bounces due to lack of immediate AI engagement.",
                                        "fomo_intelligence": "Direct AI outreach delivers exclusive leads at 1/10th the cost of your current Google Ad spend."
                                    }
                                })
            except Exception as e:
                print(f"Error scraping {city}: {e}")
                
            context.close()
            time.sleep(3) # evading bans
            
        browser.close()
        
    print(f"\n🔥 SUCCESS: Secured {len(leads)} high-intent businesses paying for ads.")
    
    if leads:
        os.makedirs("data", exist_ok=True)
        with open("data/researched_leads.json", "w") as f:
            json.dump(leads, f, indent=2)
            
        print("Pushing hot leads through CRM Pipeline...")
        subprocess.run([sys.executable, "src/email_generator.py"])
        subprocess.run([sys.executable, "src/excel_manager.py"])
        print("Updating Dashboard...")
        import pandas as pd
        try:
            excel_filename = f"{INDUSTRY_TARGET.capitalize()}_Industry_Master.xlsx"
            df = pd.read_excel(excel_filename, sheet_name="CRM_SYNC")
            df = df.fillna('')
            with open("dashboard/crm_data.json", "w", encoding="utf-8") as f:
                json.dump(df.to_dict(orient='records'), f, indent=2)
            print("DONE. Check Dashbard!")
        except Exception as e: pass

if __name__ == "__main__":
    scrape_hot_ads()
