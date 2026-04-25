import pandas as pd
import os

def prepare_all_for_sending(excel_file="AI_Growth_Engine_MASTER.xlsx"):
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found.")
        return

    # Load all sheets to preserve them
    with pd.ExcelFile(excel_file) as xls:
        df_strategy = pd.read_excel(xls, sheet_name='STRATEGY_INTEL')
        df_crm = pd.read_excel(xls, sheet_name='CRM_SYNC')

    # Mark all as SEND
    df_crm['Action'] = 'SEND'
    
    # Save back
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df_strategy.to_excel(writer, sheet_name='STRATEGY_INTEL', index=False)
        df_crm.to_excel(writer, sheet_name='CRM_SYNC', index=False)
    
    print(f"Success: All {len(df_crm)} leads in '{excel_file}' are now marked for sending!")

if __name__ == "__main__":
    prepare_all_for_sending()
