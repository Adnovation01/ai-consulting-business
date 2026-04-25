import json
import os

def generate_social_content(input_file="data/researched_leads.json"):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r') as f:
        leads = json.load(f)

    print("Generating LinkedIn marketing content based on recent research...")
    
    # Generic Post 1: The Opportunity
    post1 = {
        "title": "The AI Gap in E-commerce",
        "content": (
            "Did you know that 3 out of 5 top Shopify stores still rely on manual product descriptions?\n\n"
            "After researching 5 key niches (Home Decor, Fashion, Beauty, Electronics, Health), "
            "the biggest 'AI Gap' is in personalized search and automated customer support.\n\n"
            "Small changes like implementing a semantic search engine can boost ROI by up to 20%.\n\n"
            "#AI #Ecommerce #GrowthMarketing #Automation"
        )
    }

    # Generic Post 2: Specific Niche Focus
    post2 = {
        "title": "Home Decor AI Revolution",
        "content": (
            "Visual search is no longer a 'nice-to-have' for Home Decor brands.\n\n"
            "Recent internal research shows that brands like Zen Flora could see a massive lift "
            "just by adding AI-powered interior design assistants.\n\n"
            "The future of shopping is assistive, not just transactional.\n\n"
            "#HomeDecor #AIIntegration #RetailTech"
        )
    }

    marketing_plan = [post1, post2]
    
    output_file = "data/marketing_content.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(marketing_plan, f, indent=4)
        
    print(f"Marketing content saved to {output_file}")
    for post in marketing_plan:
        print(f"\n--- {post['title']} ---\n{post['content']}\n")

if __name__ == "__main__":
    generate_social_content()
