"""
Lead Scraping Engine — powered by Hotfrog.com
Hotfrog is accessible from server IPs (no Cloudflare block).
Flow: Hotfrog search -> profile page -> real website -> extract email -> save to DB
"""
import os, json, time, re, random, sys
import requests
from bs4 import BeautifulSoup

# Force UTF-8 so Windows cp1252 never crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.database_manager import save_lead

INDUSTRY_TARGET = sys.argv[1] if len(sys.argv) > 1 else "dentist"

ALL_STATES = [
    ('AL','Alabama',['Birmingham','Huntsville','Mobile']),
    ('AK','Alaska',['Anchorage']),
    ('AZ','Arizona',['Phoenix','Tucson','Scottsdale']),
    ('AR','Arkansas',['Little Rock','Fayetteville']),
    ('CA','California',['Los Angeles','San Diego','San Jose','Sacramento','San Francisco']),
    ('CO','Colorado',['Denver','Colorado Springs']),
    ('CT','Connecticut',['Bridgeport','New Haven','Hartford']),
    ('DE','Delaware',['Wilmington']),
    ('FL','Florida',['Miami','Orlando','Tampa','Jacksonville','Fort Lauderdale']),
    ('GA','Georgia',['Atlanta','Augusta','Savannah']),
    ('HI','Hawaii',['Honolulu']),
    ('ID','Idaho',['Boise']),
    ('IL','Illinois',['Chicago','Aurora','Naperville']),
    ('IN','Indiana',['Indianapolis','Fort Wayne']),
    ('IA','Iowa',['Des Moines','Cedar Rapids']),
    ('KS','Kansas',['Wichita','Overland Park']),
    ('KY','Kentucky',['Louisville','Lexington']),
    ('LA','Louisiana',['New Orleans','Baton Rouge']),
    ('ME','Maine',['Portland']),
    ('MD','Maryland',['Baltimore']),
    ('MA','Massachusetts',['Boston','Worcester']),
    ('MI','Michigan',['Detroit','Grand Rapids']),
    ('MN','Minnesota',['Minneapolis','Saint Paul']),
    ('MS','Mississippi',['Jackson']),
    ('MO','Missouri',['Kansas City','Saint Louis']),
    ('MT','Montana',['Billings']),
    ('NE','Nebraska',['Omaha','Lincoln']),
    ('NV','Nevada',['Las Vegas','Henderson','Reno']),
    ('NH','New Hampshire',['Manchester']),
    ('NJ','New Jersey',['Newark','Jersey City']),
    ('NM','New Mexico',['Albuquerque']),
    ('NY','New York',['New York City','Buffalo','Rochester']),
    ('NC','North Carolina',['Charlotte','Raleigh','Durham']),
    ('ND','North Dakota',['Fargo']),
    ('OH','Ohio',['Columbus','Cleveland','Cincinnati']),
    ('OK','Oklahoma',['Oklahoma City','Tulsa']),
    ('OR','Oregon',['Portland','Salem']),
    ('PA','Pennsylvania',['Philadelphia','Pittsburgh']),
    ('RI','Rhode Island',['Providence']),
    ('SC','South Carolina',['Columbia','Charleston']),
    ('SD','South Dakota',['Sioux Falls']),
    ('TN','Tennessee',['Nashville','Memphis']),
    ('TX','Texas',['Houston','San Antonio','Dallas','Austin']),
    ('UT','Utah',['Salt Lake City','Provo']),
    ('VT','Vermont',['Burlington']),
    ('VA','Virginia',['Virginia Beach','Richmond']),
    ('WA','Washington',['Seattle','Spokane']),
    ('WV','West Virginia',['Charleston']),
    ('WI','Wisconsin',['Milwaukee','Madison']),
    ('WY','Wyoming',['Cheyenne']),
]

PAIN_POINTS = [
    "No real-time online booking — losing est. 31% of after-hours demand",
    "Website loads >5s on mobile — penalising local SEO rank",
    "No AI chatbot — 68% of customers won't call if chat unavailable",
    "Google Business Profile has <50 reviews vs category leaders",
    "No customer reactivation automation — est. $14k/yr lost from dormant records",
    "No mobile-first CTA — 70%+ of local search traffic is mobile",
    "No Google LSA ads — invisible above organic results",
    "Booking requires phone + callback — 4+ friction points before first visit",
]
MARKET_GAPS = [
    "Top local competitors run Google LSA ads — this business is organic only.",
    "Corporate chains expanding aggressively locally — independents losing market share.",
    "Competitor 1.2 miles away launched AI intake and reported +22% new patient calls.",
    "64% of patients in this area check Google Maps before calling — no review strategy found.",
]

_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

def _session():
    s = requests.Session()
    # NOTE: Do NOT set Accept-Encoding — requests handles decompression automatically.
    # Setting it manually breaks gzip/br decompression.
    s.headers.update({
        'User-Agent': random.choice(_UAS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    })
    return s

def _slug(city, state_code):
    """e.g. 'New York', 'NY' -> 'new-york--ny'"""
    return f"{city.lower().replace(' ', '-')}--{state_code.lower()}"

def scrape_hotfrog_search(session, industry, city, state_code, page=1):
    """Return list of {name, profile_url, website, phone} from one Hotfrog search page."""
    slug = _slug(city, state_code)
    url = f"https://www.hotfrog.com/search/{slug}/{requests.utils.quote(industry)}?page={page}"
    try:
        r = session.get(url, timeout=20)
        if r.status_code != 200:
            print(f"  [HF] HTTP {r.status_code} for {city},{state_code}")
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        boxes = soup.select('.hf-box')
        if not boxes:
            print(f"  [HF] No listings on page {page} for {city},{state_code}")
            return []

        results = []
        for box in boxes:
            name_el = box.select_one('h4') or box.select_one('h3') or box.select_one('.h6')
            links = box.select('a')
            profile = next(
                (l.get('href', '') for l in links if '/company/' in l.get('href', '')), ''
            )
            website = next(
                (l.get('href', '') for l in links
                 if l.get('href', '').startswith('http')
                 and 'hotfrog' not in l.get('href', '')
                 and l.get('href', '') != 'https://#'), ''
            )
            phone_match = re.search(r'[\+\(]?\d[\d\s\-\.\(\)]{7,15}\d', box.get_text())
            phone = phone_match.group(0).strip() if phone_match else ''
            name = name_el.get_text(strip=True) if name_el else ''
            if name and profile:
                results.append({
                    'name': name,
                    'profile_url': ('https://www.hotfrog.com' + profile
                                    if profile.startswith('/') else profile),
                    'website': website,
                    'phone': phone,
                })
        return results
    except requests.RequestException as e:
        print(f"  [HF] Request error: {str(e)[:80]}")
        return []

_SKIP_DOMAINS = {
    'hotfrog', 'google.com', 'facebook.com', 'twitter.com', 'instagram.com',
    'linkedin.com', 'jooble.org', 'centralindex.com', 'locafy.com',
    'newfold.com', 'here.com', 'yelp.com', 'yellowpages.com', 'tripadvisor',
    'foursquare', 'bbb.org', 'angieslist', 'thumbtack', 'homeadvisor',
    'healthgrades', 'zocdoc', 'vitals.com', 'ratemds', 'webmd.com',
    'maps.google', 'share.here', 'assets.centralindex',
}

def _is_real_business_site(href):
    """Return True if href looks like a real business website (not a directory/social/map)."""
    if not href or not href.startswith('http'):
        return False
    return not any(skip in href.lower() for skip in _SKIP_DOMAINS)

def get_website_from_profile(session, profile_url):
    """Visit the Hotfrog profile page to get the real business website URL."""
    try:
        r = session.get(profile_url, timeout=15)
        if r.status_code != 200:
            return ''
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.select('a[href]'):
            href = a.get('href', '')
            if _is_real_business_site(href):
                return href
    except Exception:
        pass
    return ''

def google_find_website(session, business_name, city, state_code):
    """Search DuckDuckGo to find the official website of a business."""
    try:
        query = f'{business_name} {city} {state_code} official site'
        url = f'https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}'
        r = session.get(url, timeout=12)
        if r.status_code != 200:
            return ''
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.select('a.result__url, a.result__a, .result__url'):
            href = a.get('href', '') or a.get_text(strip=True)
            if href.startswith('http') and _is_real_business_site(href):
                return href
    except Exception:
        pass
    return ''

def extract_email(session, url):
    """Extract first valid business email from a website."""
    if not url or not url.startswith('http'):
        return ''
    try:
        r = session.get(url, timeout=12, allow_redirects=True)
        if r.status_code != 200:
            return ''
        pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        skip = {'wix', '.png', '.jpg', '.gif', 'sentry', 'example',
                'domain', 'test', 'sitedomain', 'cloudflare', 'wordpress',
                'schema', 'jquery', 'googleapis', 'bootstrap', 'noreply'}
        emails = [e.lower() for e in set(re.findall(pattern, r.text))
                  if not any(s in e.lower() for s in skip)]
        if emails:
            return emails[0]
        # Try /contact page
        soup = BeautifulSoup(r.text, 'html.parser')
        contact_href = next(
            (a['href'] for a in soup.select('a[href]')
             if 'contact' in a.get('href', '').lower()), None
        )
        if contact_href:
            if not contact_href.startswith('http'):
                contact_href = url.rstrip('/') + '/' + contact_href.lstrip('/')
            try:
                r2 = session.get(contact_href, timeout=10)
                emails2 = [e.lower() for e in set(re.findall(pattern, r2.text))
                           if not any(s in e.lower() for s in skip)]
                if emails2:
                    return emails2[0]
            except Exception:
                pass
    except Exception:
        pass
    return ''

def build_lead(raw, city, state_code, industry, website, email):
    pct = random.randint(8, 15)
    monthly = round(850000 / 12 * pct / 100 / 100) * 100
    return {
        'name': raw['name'],
        'url': website,
        'email': email,
        'location': f"{city}, {state_code}",
        'niche': industry.capitalize(),
        'analysis': {
            'hard_pain_points': random.sample(PAIN_POINTS, 2),
            'estimated_revenue_leak': f"${monthly:,}/mo (~{pct}%)",
            'market_gap_analysis': random.choice(MARKET_GAPS),
            'conversion_friction': 'Requires manual phone calls for appointments.',
            'fomo_intelligence': 'AI automated booking is capturing local customers.',
        }
    }

def scrape_state(state_tuple, industry):
    code, name, cities = state_tuple
    print(f"\n[{code}] {name} — scraping {industry}...")
    session = _session()
    state_leads = []

    for city in cities:
        if len(state_leads) >= 25:
            break
        for page in range(1, 4):
            if len(state_leads) >= 25:
                break
            raw_list = scrape_hotfrog_search(session, industry, city, code, page=page)
            if not raw_list:
                break

            print(f"  [{code}] {city} p{page}: {len(raw_list)} raw listings")

            for raw in raw_list:
                if len(state_leads) >= 25:
                    break
                print(f"    > {raw['name'][:55]}")

                # Get website: from search result -> profile page -> DuckDuckGo fallback
                website = raw.get('website', '')
                if not website or not _is_real_business_site(website):
                    website = get_website_from_profile(session, raw['profile_url'])
                if not website:
                    website = google_find_website(session, raw['name'], city, code)

                # Extract email from website
                email = ''
                if website:
                    email = extract_email(session, website)
                    if email:
                        print(f"      Email: {email}")

                lead = build_lead(raw, city, code, industry, website, email)
                try:
                    save_lead(lead)
                    state_leads.append(lead)
                    print(f"      Saved to DB (email: {'yes' if email else 'pending'})")
                except Exception as e:
                    print(f"      DB error: {str(e)[:60]}")

                time.sleep(random.uniform(0.8, 2.0))

            time.sleep(random.uniform(1.5, 3.0))

    print(f"[{code}] Done — {len(state_leads)} leads saved")
    return state_leads

def main():
    os.makedirs('data', exist_ok=True)
    industry = INDUSTRY_TARGET.lower().strip()
    all_leads = []

    print(f"NATIONWIDE SCRAPE: {industry.capitalize()} across all 50 US states")
    print(f"Source: hotfrog.com (Cloudflare-free directory)")
    print("=" * 60)

    for state in ALL_STATES:
        leads = scrape_state(state, industry)
        all_leads.extend(leads)
        # Live JSON backup after each state
        with open('data/researched_leads.json', 'w', encoding='utf-8') as f:
            json.dump(all_leads, f, indent=2, ensure_ascii=False)
        idx = ALL_STATES.index(state) + 1
        print(f"Progress: {idx}/50 states | Total leads: {len(all_leads)}\n")

    print(f"\nCOMPLETE — {len(all_leads)} total leads saved to database")

if __name__ == '__main__':
    main()
