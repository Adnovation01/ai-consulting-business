import json
import os
import time
from playwright.sync_api import sync_playwright

def scrape_yellowpages(city, state, query="dentist", target_count=50):
    leads = []
    print(f"SEARCH: Scraping {target_count} {query}s in {city}, {state} via Playwright...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        current_page = 1
        
        while len(leads) < target_count and current_page <= 5:
            url = f"https://www.yellowpages.com/search?search_terms={query}&geo_location_terms={city}%2C+{state}&page={current_page}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Wait for results to be visible
                page.wait_for_selector(".result", timeout=10000)
                
                results = page.query_selector_all(".result")
                if not results:
                    break
                    
                for result in results:
                    if len(leads) >= target_count:
                        break
                        
                    name_elem = result.query_selector(".business-name")
                    name = name_elem.inner_text() if name_elem else None
                    
                    website_elem = result.query_selector("a.track-visit-website")
                    website = website_elem.get_attribute("href") if website_elem else None
                    
                    if name and website:
                        # Clean up formatting
                        name = name.strip()
                        leads.append({
                            "name": name,
                            "url": website,
                            "location": f"{city}, {state}",
                            "niche": "Dentist"
                        })
                        print(f"      + Found: {name}")
                current_page += 1
            except Exception as e:
                print(f"  -> Error or no more results on page {current_page}: {e}")
                break
                
        browser.close()
        
    print(f"OK: Found {len(leads)} valid leads with websites in {city}.")
    return leads

def run_scraper():
    alabama_leads = []
    cities = ["Birmingham", "Huntsville", "Mobile"]
    
    for city in cities:
        needed = 50 - len(alabama_leads)
        if needed <= 0: break
        
        target = min(20, needed) 
        batch = scrape_yellowpages(city, "AL", "dentist", target_count=target)
        alabama_leads.extend(batch)
        time.sleep(1)
        
    os.makedirs("data", exist_ok=True)
    with open("data/leads.json", "w", encoding="utf-8") as f:
        json.dump(alabama_leads, f, indent=4)
        
    print(f"\nSUCCESS: Extracted a total of {len(alabama_leads)} raw leads for Alabama.")
    print("These are now ready for the Deep Audit Engine.")

if __name__ == "__main__":
    run_scraper()
