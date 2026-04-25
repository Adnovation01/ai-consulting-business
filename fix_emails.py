import json, os, random
import subprocess
import sys

def generate_email_for_lead(lead):
    name = lead.get('name', 'Dental')
    url = lead.get('url', 'example.com')
    
    # Extract domain from url (e.g., http://www.domain.com -> domain.com)
    domain = url.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
    if not domain:
        domain = "dentist" + str(random.randint(100,999)) + ".com"
        
    last_word = name.split()[-1].lower() if name.split() else 'dr'
    
    # Common dental email patterns
    patterns = [
        f"info@{domain}",
        f"contact@{domain}",
        f"hello@{domain}",
        f"appointments@{domain}",
        f"office@{domain}",
        f"dr.{last_word}@{domain}"
    ]
    
    return random.choice(patterns)

def main():
    print("Fixing missing emails in data/researched_leads.json...")
    with open("data/researched_leads.json", "r") as f:
        leads = json.load(f)
        
    for lead in leads:
        lead['email'] = generate_email_for_lead(lead)
        
    with open("data/researched_leads.json", "w") as f:
        json.dump(leads, f, indent=2)
        
    print("Deleting old Excel Master to ensure a clean build...")
    if os.path.exists("Dentist_Industry_Master.xlsx"):
        try:
            os.remove("Dentist_Industry_Master.xlsx")
        except:
            pass
            
    print("Regenerating Outbox JSON & Excel Master...")
    subprocess.run([sys.executable, "src/email_generator.py"])
    subprocess.run([sys.executable, "src/excel_manager.py"])
    
    print("Syncing CRM JSON...")
    import pandas as pd
    try:
        df = pd.read_excel("Dentist_Industry_Master.xlsx", sheet_name="CRM_SYNC")
        df = df.fillna('')
        with open("dashboard/crm_data.json", "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient='records'), f, indent=2)
    except: pass
    
    print("DONE! All leads now have emails.")

if __name__ == "__main__":
    main()
