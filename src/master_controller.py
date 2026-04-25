import json
import os
import subprocess
import time

# List of all 50 US States
STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", 
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", 
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", 
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", 
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", 
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", 
    "Wisconsin", "Wyoming"
]

def run_engine_for_state(state, niche="Dentist"):
    print(f"\n" + "="*50)
    print(f"CAMPAIGN: {niche} in {state}")
    print("="*50 + "\n")
    
    # Step 1: Lead Discovery
    # Note: For the first states, we use bootstrap data.
    print(f"Step 1: Processing {state}...")
    # Map state to bootstrap file if exists
    bootstrap_file = f"data/{state.lower()}_bootstrap.json"
    cmd = ["python", "src/lead_finder.py", "--niche", niche, "--location", state]
    if os.path.exists(bootstrap_file):
        cmd.extend(["--import_file", bootstrap_file])
    
    subprocess.run(cmd)
    
    # Step 2: AI Research & Audit
    print(f"Step 2: Performing Deep AI Audits for {state}...")
    subprocess.run(["python", "src/lead_researcher.py"])
    
    # Step 3: Personalized Email Generation
    print(f"Step 3: Drafting Emails for {state}...")
    subprocess.run(["python", "src/email_generator.py"])
    
    # Step 4: Master Export
    print(f"Step 4: Syncing to Master Excel...")
    subprocess.run(["python", "src/excel_manager.py"])
    
    print(f"\nOK: COMPLETED State: {state}\n")

def main():
    print("--- NATIONWIDE AI CONSULTING ENGINE INITIALIZED ---")
    
    for state in STATES:
        # For demo, we only run those with bootstrap data unless user wants a full crawl
        bootstrap_file = f"data/{state.lower()}_bootstrap.json"
        if os.path.exists(bootstrap_file):
            run_engine_for_state(state)
        else:
            # Skip states without data for now, or we can prompt a search
            pass

if __name__ == "__main__":
    main()
