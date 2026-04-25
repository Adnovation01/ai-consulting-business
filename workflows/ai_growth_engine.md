---
description: How to run the automated AI growth engine for your consulting business.
---

# AI Sales & Marketing Engine Workflow

Follow these steps to find, research, and contact potential clients using the AI engine.

1. **Configure Target Niche**
   - Edit the configuration in `lead_finder.py` to specify your target niche and location (e.g., "Chicago Law Firms" or "Shopify Stores").

2. **Run Lead Identification**
   // turbo
   - Run `python src/lead_finder.py` to generate the initial list of potential clients.

3. **Run AI Research**
   // turbo
   - Run `python src/lead_researcher.py` to analyze the websites of the discovered leads and identify AI integration gaps.

4. **Generate & Review Outreach**
   - Run `python src/email_generator.py` to create personalized email drafts.
   - [Optional] Manually review the `outbox.json` file to ensure the AI's tone is perfect.

5. **Execute Outreach**
   // turbo
   - Run `python src/outreach_manager.py --send` to transmit the emails to the leads.

6. **Track Results**
   - Check the `crm_status.xlsx` or Google Sheet to monitor responses and book meetings.
