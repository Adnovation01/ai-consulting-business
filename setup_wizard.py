import os

def run_wizard():
    print("====================================")
    print("🚀 AI GROWTH ENGINE SETUP WIZARD 🚀")
    print("====================================\n")
    print("This will help you set up your AI Consulting Business automation in 60 seconds.\n")

    name = input("1. What is your Name? [Default: Pranshu]: ") or "Pranshu"
    title = input("2. What is your Professional Title? [Default: AI Consultant]: ") or "AI Consultant"
    website = input("3. What is your Website URL? (Optional): ")
    niche = input("4. What Industry do you want to target first? [Default: Shopify Stores]: ") or "Shopify Stores"
    location = input("5. What Location (City/State)? [Default: California]: ") or "California"
    
    openai_key = input("\n6. Paste your OpenAI API Key (starts with sk-): ")
    resend_key = input("7. Paste your Resend API Key (starts with re-): ")
    from_email = input("8. Which email address will you send from? (e.g., hello@yourdomain.com): ")

    env_content = f"""# --- AI Growth Engine Configuration ---

# 1. AI Power (OpenAI)
OPENAI_API_KEY={openai_key}

# 2. Email Outreach (Resend)
RESEND_API_KEY={resend_key}
FROM_EMAIL={from_email}

# 3. Personal Branding
YOUR_NAME={name}
YOUR_TITLE={title}
YOUR_WEBSITE={website}

# 4. Target Search
DEFAULT_NICHE={niche}
DEFAULT_LOCATION={location}
"""

    with open(".env", "w") as f:
        f.write(env_content)

    print("\n✅ Setup Complete! A '.env' file has been created.")
    print("You can now run the engine by double-clicking 'START_ENGINE.bat'.")

if __name__ == "__main__":
    run_wizard()
