import json
import os
import pandas as pd

def generate_dashboard(crm_file="data/crm_status.csv", output_file="RESULTS.md"):
    if not os.path.exists(crm_file):
        print(f"Error: {crm_file} not found. Run the engine first!")
        return

    df = pd.read_csv(crm_file)
    
    dashboard_content = f"""# 📈 AI Growth Engine: Performance Dashboard

Last Updated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}

## 🚀 Campaign Summary
- **Total Leads Processed**: {len(df)}
- **Emails Sent**: {len(df[df['Status'] == 'SENT'])}
- **Pending Replies**: {len(df[df['Reply Status'] == 'PENDING'])}

## 🎯 Recent Leads & Actions
| Company | Niche | Status | Action Taken |
| :--- | :--- | :--- | :--- |
"""
    for _, row in df.iterrows():
        dashboard_content += f"| {row['Company']} | {row['Lead Category']} | {row['Status']} | Personalized Email Sent |\n"

    dashboard_content += """
---
## 💡 Next Steps
1. Check your email inbox for replies.
2. If a lead replies, mark them as 'INTERESTED' in the CSV file.
3. Use the `content_generator.py` to post the generated LinkedIn updates.
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(dashboard_content)
    
    print(f"Dashboard updated: {output_file}")

if __name__ == "__main__":
    generate_dashboard()
