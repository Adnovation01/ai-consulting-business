import json
import os
import pandas as pd
from openpyxl import load_workbook

def get_state_full_name(state_code):
    states = {
        'AK': 'Alaska', 'AL': 'Alabama', 'AR': 'Arkansas', 'AZ': 'Arizona', 'CA': 'California',
        'CO': 'Colorado', 'CT': 'Connecticut', 'DC': 'District of Columbia', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'IA': 'Iowa', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana',
        'MA': 'Massachusetts', 'MD': 'Maryland', 'ME': 'Maine', 'MI': 'Michigan', 'MN': 'Minnesota',
        'MO': 'Missouri', 'MS': 'Mississippi', 'MT': 'Montana', 'NC': 'North Carolina',
        'ND': 'North Dakota', 'NE': 'Nebraska', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
        'NM': 'New Mexico', 'NV': 'Nevada', 'NY': 'New York', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VA': 'Virginia',
        'VT': 'Vermont', 'WA': 'Washington', 'WI': 'Wisconsin', 'WV': 'West Virginia', 'WY': 'Wyoming'
    }
    return states.get(state_code.upper(), state_code)

def generate_exports(input_file="data/outbox.json"):
    """
    Groups leads by state and appends to niche-specific Excel files.
    Also creates a CRM_SYNC tab for email outreach.
    """
    if not os.path.exists(input_file): return

    with open(input_file, 'r', encoding='utf-8') as f:
        leads = json.load(f)
    if not leads: return

    # Grouping logic
    organized_data = {}
    for lead in leads:
        niche = lead.get('niche', 'Business').replace(" ", "_").capitalize()
        raw_loc = lead.get('location', 'Unknown')
        state_code = raw_loc.split(',')[-1].strip() if ',' in raw_loc else raw_loc
        state_name = get_state_full_name(state_code).replace(" ", "_")
        
        if niche not in organized_data: organized_data[niche] = {}
        if state_name not in organized_data[niche]: organized_data[niche][state_name] = []
            
        analysis = lead.get('analysis', {})
        pains = analysis.get('hard_pain_points', [])
        
        row = {
            "Business Name": lead['name'],
            "Website": lead['url'],
            "Email Address": lead.get('email', 'Pending Audit'),
            "Strategic Gap": analysis.get('market_gap_analysis', 'N/A'),
            "Revenue Leak": analysis.get('estimated_revenue_leak', 'N/A'),
            "Pain Point 1": pains[0] if len(pains) > 0 else "N/A",
            "Pain Point 2": pains[1] if len(pains) > 1 else "N/A",
            "Pain Point 3": pains[2] if len(pains) > 2 else "N/A",
            "Friction Hub": analysis.get('conversion_friction', 'N/A'),
            "Draft Subject": lead.get('email_draft', {}).get('subject', 'N/A'),
            "Draft Body": lead.get('email_draft', {}).get('body', 'N/A')
        }
        organized_data[niche][state_name].append(row)

    # Master Industry Export
    for niche, states_dict in organized_data.items():
        excel_file = f"{niche}_Industry_Master.xlsx"
        
        # Collect all rows for the final CRM_SYNC tab
        all_sync_rows = []

        for state_name, rows in states_dict.items():
            df = pd.DataFrame(rows)
            
            # 1. Update State Tab
            if os.path.exists(excel_file):
                with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=state_name, index=False)
            else:
                df.to_excel(excel_file, sheet_name=state_name, index=False)

            # Prepare rows for sync
            for r in rows:
                all_sync_rows.append({
                    "Lead Name": r["Business Name"],
                    "Website": r["Website"],
                    "Email": r["Email Address"],
                    "State": state_name,
                    "Leak ($)": r["Revenue Leak"],
                    "Draft Subject": r["Draft Subject"],
                    "Draft Body": r["Draft Body"],
                    "Action": "READY", # READY -> SEND
                    "Status": "Pending Outreach",
                    "Sent At": ""
                })

        # 2. Update CRM_SYNC Tab (Unified list for outreach)
        if all_sync_rows:
            sync_df = pd.DataFrame(all_sync_rows)
            # Use 'overlay' or 'replace' for the whole tab to ensure it's up to date
            with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                try:
                    # If file exists and we are in mode 'a', we can just write the sheet
                    sync_df.to_excel(writer, sheet_name='CRM_SYNC', index=False)
                except Exception:
                    # If it's a new file, we'd handle it differently but the loop above creates it
                    sync_df.to_excel(writer, sheet_name='CRM_SYNC', index=False)

    print(f"OK: Nationwide Master Synced for {len(leads)} leads.")

if __name__ == "__main__":
    generate_exports()
