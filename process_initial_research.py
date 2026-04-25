import json
import os
from src.lead_researcher import deep_audit

def main():
    with open("data/leads.json", "r") as f:
        leads = json.load(f)[:5]
        
    with open("data/scraped_content.json", "r") as f:
        scraped_content = json.load(f)
        
    researched_leads = []
    for lead in leads:
        url = lead['url']
        content = scraped_content.get(url, "")
        lead['analysis'] = deep_audit(lead['name'], url, lead['niche'], website_content=content)
        researched_leads.append(lead)
        
    with open("data/researched_leads.json", "w") as f:
        json.dump(researched_leads, f, indent=4)
        
    print("DONE: Researched 5 leads with real content.")

if __name__ == "__main__":
    main()
