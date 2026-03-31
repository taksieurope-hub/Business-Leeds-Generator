"""
Comprehensive Lead Seeder - Uses multiple FREE sources
- Google Maps API
- Web scraping of public business directories
- Yellow Pages, Yelp public listings
- Google Search results

Run continuously: python lead_seeder_v2.py --continuous --interval 3600
"""

import asyncio
import os
import sys
import re
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import httpx
from bs4 import BeautifulSoup
import random
import uuid
from datetime import datetime, timezone
import logging
import argparse
import json
import time

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# User agents for web scraping
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# Business categories
BUSINESS_CATEGORIES = [
    "restaurant", "cafe", "bakery", "pizza", "sushi", "bar", "pub", "brewery", "coffee shop",
    "auto repair", "car wash", "mechanic", "tire shop", "auto body shop", "car dealership",
    "hair salon", "barber shop", "nail salon", "spa", "beauty salon", "tattoo parlor",
    "dentist", "doctor", "clinic", "pharmacy", "chiropractor", "optometrist", "veterinarian",
    "gym", "fitness center", "yoga studio", "pilates", "crossfit", "martial arts", "boxing",
    "plumber", "electrician", "hvac", "roofing", "landscaping", "handyman", "contractor",
    "cleaning service", "maid service", "carpet cleaning", "pressure washing", "window cleaning",
    "pet grooming", "pet store", "dog training", "pet boarding", "pet daycare",
    "florist", "gift shop", "jewelry store", "clothing store", "shoe store", "boutique",
    "furniture store", "hardware store", "electronics repair", "computer repair", "phone repair",
    "accounting", "lawyer", "insurance agent", "real estate agent", "financial advisor",
    "photographer", "wedding planner", "event venue", "catering", "dj service", "florist",
    "tutoring", "music lessons", "dance studio", "art classes", "driving school", "language school",
    "daycare", "preschool", "after school program", "summer camp", "nanny service",
    "printing shop", "sign shop", "tailor", "dry cleaner", "laundromat", "shoe repair",
    "locksmith", "moving company", "storage facility", "shipping store", "courier service",
    "travel agency", "hotel", "motel", "bed and breakfast", "hostel", "vacation rental",
    "construction company", "architect", "interior designer", "home staging",
    "massage therapy", "acupuncture", "physical therapy", "counselor", "psychologist",
    "ice cream shop", "donut shop", "bagel shop", "deli", "butcher", "seafood market",
    "wine shop", "liquor store", "convenience store", "grocery store", "farmers market",
    "bookstore", "toy store", "sporting goods", "bike shop", "surf shop", "outdoor gear",
    "auto parts store", "motorcycle shop", "boat dealer", "rv dealer",
    "music store", "art supply store", "craft store", "fabric store",
    "appliance repair", "furniture repair", "upholstery", "antique store",
    "pawn shop", "thrift store", "consignment shop",
    "towing service", "roadside assistance", "car rental",
    "pest control", "tree service", "lawn care", "pool service",
    "security company", "alarm installation", "camera installation",
    "solar installation", "window installation", "door installation",
    "painting contractor", "flooring contractor", "tile contractor",
    "kitchen remodeling", "bathroom remodeling", "basement finishing"
]

# Global cities for searching
GLOBAL_CITIES = [
    # USA Major Cities
    "New York NY", "Los Angeles CA", "Chicago IL", "Houston TX", "Phoenix AZ",
    "Philadelphia PA", "San Antonio TX", "San Diego CA", "Dallas TX", "San Jose CA",
    "Austin TX", "Jacksonville FL", "Fort Worth TX", "Columbus OH", "Charlotte NC",
    "San Francisco CA", "Indianapolis IN", "Seattle WA", "Denver CO", "Boston MA",
    "Nashville TN", "Detroit MI", "Portland OR", "Las Vegas NV", "Memphis TN",
    "Louisville KY", "Baltimore MD", "Milwaukee WI", "Albuquerque NM", "Tucson AZ",
    "Fresno CA", "Sacramento CA", "Atlanta GA", "Miami FL", "Oakland CA",
    "Minneapolis MN", "Cleveland OH", "New Orleans LA", "Tampa FL", "Pittsburgh PA",
    "Cincinnati OH", "St Louis MO", "Orlando FL", "Honolulu HI", "Kansas City MO",
    "Omaha NE", "Raleigh NC", "Virginia Beach VA", "Colorado Springs CO", "Tulsa OK",
    "Arlington TX", "Bakersfield CA", "Aurora CO", "Anaheim CA", "Santa Ana CA",
    "Riverside CA", "Corpus Christi TX", "Lexington KY", "Henderson NV", "Stockton CA",
    "Saint Paul MN", "Newark NJ", "Greensboro NC", "Buffalo NY", "Plano TX",
    "Lincoln NE", "Anchorage AK", "Durham NC", "Jersey City NJ", "Chandler AZ",
    
    # USA Medium Cities
    "Boise ID", "Salt Lake City UT", "Reno NV", "Spokane WA", "Eugene OR",
    "Santa Fe NM", "Charleston SC", "Savannah GA", "Asheville NC", "Burlington VT",
    "Providence RI", "Hartford CT", "Syracuse NY", "Rochester NY", "Albany NY",
    "Richmond VA", "Norfolk VA", "Knoxville TN", "Chattanooga TN", "Mobile AL",
    "Little Rock AR", "Jackson MS", "Baton Rouge LA", "Shreveport LA", "Biloxi MS",
    
    # Canada
    "Toronto Canada", "Vancouver Canada", "Montreal Canada", "Calgary Canada",
    "Edmonton Canada", "Ottawa Canada", "Winnipeg Canada", "Quebec City Canada",
    "Hamilton Canada", "Halifax Canada", "Victoria Canada", "Saskatoon Canada",
    "Regina Canada", "St Johns Canada", "Kelowna Canada", "Barrie Canada",
    
    # UK
    "London UK", "Manchester UK", "Birmingham UK", "Leeds UK", "Glasgow UK",
    "Liverpool UK", "Bristol UK", "Sheffield UK", "Edinburgh UK", "Cardiff UK",
    "Belfast UK", "Newcastle UK", "Nottingham UK", "Southampton UK", "Brighton UK",
    "Leicester UK", "Portsmouth UK", "Plymouth UK", "Reading UK", "Derby UK",
    
    # Australia
    "Sydney Australia", "Melbourne Australia", "Brisbane Australia", "Perth Australia",
    "Adelaide Australia", "Gold Coast Australia", "Canberra Australia", "Hobart Australia",
    "Darwin Australia", "Cairns Australia", "Newcastle Australia", "Wollongong Australia",
    "Geelong Australia", "Townsville Australia", "Toowoomba Australia",
    
    # New Zealand
    "Auckland New Zealand", "Wellington New Zealand", "Christchurch New Zealand",
    "Hamilton New Zealand", "Tauranga New Zealand", "Dunedin New Zealand",
    
    # Ireland
    "Dublin Ireland", "Cork Ireland", "Galway Ireland", "Limerick Ireland", "Waterford Ireland",
    
    # Germany
    "Berlin Germany", "Munich Germany", "Hamburg Germany", "Frankfurt Germany",
    "Cologne Germany", "Stuttgart Germany", "Dusseldorf Germany", "Leipzig Germany",
    
    # France
    "Paris France", "Lyon France", "Marseille France", "Toulouse France",
    "Nice France", "Bordeaux France", "Lille France", "Nantes France",
    
    # Spain
    "Madrid Spain", "Barcelona Spain", "Valencia Spain", "Seville Spain",
    "Bilbao Spain", "Malaga Spain", "Zaragoza Spain", "Alicante Spain",
    
    # Italy
    "Rome Italy", "Milan Italy", "Naples Italy", "Turin Italy", "Florence Italy",
    "Bologna Italy", "Venice Italy", "Verona Italy", "Genoa Italy",
    
    # Netherlands
    "Amsterdam Netherlands", "Rotterdam Netherlands", "The Hague Netherlands",
    "Utrecht Netherlands", "Eindhoven Netherlands",
    
    # South Africa
    "Johannesburg South Africa", "Cape Town South Africa", "Durban South Africa",
    "Pretoria South Africa", "Port Elizabeth South Africa",
    
    # India
    "Mumbai India", "Delhi India", "Bangalore India", "Chennai India",
    "Kolkata India", "Hyderabad India", "Pune India", "Ahmedabad India",
    
    # UAE
    "Dubai UAE", "Abu Dhabi UAE", "Sharjah UAE",
    
    # Singapore
    "Singapore",
    
    # Philippines
    "Manila Philippines", "Cebu Philippines", "Davao Philippines",
    
    # Mexico
    "Mexico City Mexico", "Guadalajara Mexico", "Monterrey Mexico",
    "Cancun Mexico", "Tijuana Mexico", "Puebla Mexico",
    
    # Brazil
    "Sao Paulo Brazil", "Rio de Janeiro Brazil", "Brasilia Brazil",
    "Salvador Brazil", "Fortaleza Brazil", "Belo Horizonte Brazil",
]


def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }


def extract_phone(text):
    """Extract phone number from text"""
    patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\+\d{1,3}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None


def extract_website(text, soup=None):
    """Extract website from text or soup"""
    if soup:
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if 'http' in href and 'yellowpages' not in href and 'yelp' not in href:
                if any(ext in href for ext in ['.com', '.net', '.org', '.co', '.io', '.biz']):
                    return href
    
    pattern = r'https?://[^\s<>"\']+\.[a-z]{2,}'
    match = re.search(pattern, text)
    if match:
        return match.group()
    return None


def extract_country(address):
    """Extract country from address"""
    address_lower = address.lower()
    
    mappings = {
        "usa": "USA", "united states": "USA", ", us": "USA", "u.s.": "USA",
        ", ca ": "USA", ", ny ": "USA", ", tx ": "USA", ", fl ": "USA",
        ", il ": "USA", ", pa ": "USA", ", oh ": "USA", ", ga ": "USA",
        ", nc ": "USA", ", mi ": "USA", ", nj ": "USA", ", va ": "USA",
        ", wa ": "USA", ", az ": "USA", ", ma ": "USA", ", tn ": "USA",
        ", in ": "USA", ", mo ": "USA", ", md ": "USA", ", wi ": "USA",
        ", co ": "USA", ", mn ": "USA", ", sc ": "USA", ", al ": "USA",
        ", la ": "USA", ", ky ": "USA", ", or ": "USA", ", ok ": "USA",
        ", ct ": "USA", ", ut ": "USA", ", ia ": "USA", ", nv ": "USA",
        ", ar ": "USA", ", ms ": "USA", ", ks ": "USA", ", nm ": "USA",
        "canada": "Canada", "ontario": "Canada", "quebec": "Canada",
        "british columbia": "Canada", "alberta": "Canada",
        "uk": "UK", "united kingdom": "UK", "england": "UK",
        "australia": "Australia", "sydney": "Australia", "melbourne": "Australia",
        "germany": "Germany", "deutschland": "Germany",
        "france": "France", "paris": "France",
        "spain": "Spain", "madrid": "Spain", "barcelona": "Spain",
        "italy": "Italy", "roma": "Italy", "milan": "Italy",
        "netherlands": "Netherlands", "amsterdam": "Netherlands",
        "ireland": "Ireland", "dublin": "Ireland",
        "new zealand": "New Zealand", "auckland": "New Zealand",
        "south africa": "South Africa", "johannesburg": "South Africa",
        "india": "India", "mumbai": "India", "delhi": "India",
        "uae": "UAE", "dubai": "UAE", "abu dhabi": "UAE",
        "singapore": "Singapore",
        "philippines": "Philippines", "manila": "Philippines",
        "mexico": "Mexico", "ciudad de mexico": "Mexico",
        "brazil": "Brazil", "brasil": "Brazil", "sao paulo": "Brazil",
    }
    
    for key, value in mappings.items():
        if key in address_lower:
            return value
    return "USA"  # Default


def get_pitch_for_business(business):
    """Generate pitch and proposal"""
    has_website = business.get("has_website", False)
    name = business.get("business_name", "This business")
    industry = business.get("industry", "business")
    country = business.get("country", "your area")
    
    if not has_website:
        pitches = [
            f"I noticed {name} doesn't have a website yet. 80% of customers search online first - a professional website could bring you hundreds of new customers.",
            f"Hi! {name} is missing out on online customers. A modern website could increase your visibility by 300% and bring in 30-50% more business.",
            f"{name} could dominate local search results with a professional website. Your competitors have websites - let's make sure customers find YOU first.",
            f"I found {name} and see a huge opportunity. Without a website, you're invisible to billions of internet users. Let me change that.",
            f"A website for {name} would work as your 24/7 salesperson. Most {industry} businesses with websites see 40% more customers.",
        ]
        proposals = [
            f"• Professional, mobile-responsive website\n• Google Business Profile setup\n• Local SEO for {country}\n• Online booking/contact forms\n• Social media integration\n• Timeline: 2-3 weeks",
            f"• Custom website for your {industry}\n• Mobile-first design\n• Click-to-call & contact forms\n• Google Maps integration\n• SEO to rank in local searches\n• Online scheduling system",
            f"• Modern website showcasing your services\n• Fast-loading, optimized pages\n• Customer testimonials section\n• Service pages with pricing\n• Analytics to track visitors\n• Ongoing support",
        ]
        issues = [
            "No website - missing 80% of potential customers",
            "Cannot be found in Google searches",
            "No online presence vs competitors",
            "Missing online booking opportunities",
            "No way for customers to find info online"
        ]
    else:
        pitches = [
            f"I reviewed {name}'s website and found improvement opportunities. An updated design could boost conversions by 40%.",
            f"Your current website may be losing customers. Modern standards have changed - let me help you get more leads.",
            f"{name}'s website needs a refresh! 60% of traffic is mobile now - an optimized site could double your inquiries.",
        ]
        proposals = [
            f"• Website redesign with modern look\n• Mobile optimization\n• Speed improvements\n• SEO audit & fixes\n• Updated contact system\n• Security updates",
            f"• Full UX improvement\n• Clean, modern design\n• Better call-to-action buttons\n• Performance optimization\n• Analytics setup",
        ]
        issues = [
            "Website may not be mobile-friendly",
            "Outdated design patterns",
            "Page speed needs improvement",
            "SEO optimization needed",
            "Modern UX standards not met"
        ]
    
    return {
        "ai_pitch": random.choice(pitches),
        "ai_proposal": random.choice(proposals),
        "website_issues": issues
    }


# ==================== DATA SOURCES ====================

async def fetch_from_google_maps(category, city, api_key):
    """Fetch from Google Maps Places API"""
    results = []
    search_query = f"{category} in {city}"
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as http:
            response = await http.get(url, params={"query": search_query, "key": api_key})
            data = response.json()
            
            if data.get("status") != "OK":
                return []
            
            for place in data.get("results", [])[:15]:
                place_id = place.get("place_id")
                
                # Get details
                details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                try:
                    details_resp = await http.get(details_url, params={
                        "place_id": place_id,
                        "fields": "name,formatted_address,formatted_phone_number,website,geometry",
                        "key": api_key
                    })
                    details = details_resp.json().get("result", {})
                    
                    results.append({
                        "business_name": details.get("name", place.get("name")),
                        "address": details.get("formatted_address", place.get("formatted_address", "")),
                        "phone": details.get("formatted_phone_number"),
                        "website": details.get("website"),
                        "has_website": bool(details.get("website")),
                        "location": {
                            "lat": place.get("geometry", {}).get("location", {}).get("lat", 0),
                            "lng": place.get("geometry", {}).get("location", {}).get("lng", 0)
                        },
                        "industry": category.title(),
                        "country": extract_country(details.get("formatted_address", city)),
                        "source": "google_maps"
                    })
                    await asyncio.sleep(0.05)
                except:
                    continue
    except Exception as e:
        logger.error(f"Google Maps error: {e}")
    
    return results


async def scrape_yellowpages(category, city):
    """Scrape Yellow Pages (FREE)"""
    results = []
    city_slug = city.lower().replace(" ", "-").replace(",", "")
    category_slug = category.lower().replace(" ", "-")
    url = f"https://www.yellowpages.com/search?search_terms={category_slug}&geo_location_terms={city_slug}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http:
            response = await http.get(url, headers=get_random_headers())
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            listings = soup.find_all('div', class_='result')[:15]
            
            for listing in listings:
                try:
                    name_elem = listing.find('a', class_='business-name')
                    name = name_elem.get_text(strip=True) if name_elem else None
                    if not name:
                        continue
                    
                    address_elem = listing.find('div', class_='street-address')
                    locality_elem = listing.find('div', class_='locality')
                    address = ""
                    if address_elem:
                        address = address_elem.get_text(strip=True)
                    if locality_elem:
                        address += ", " + locality_elem.get_text(strip=True)
                    
                    phone_elem = listing.find('div', class_='phones')
                    phone = phone_elem.get_text(strip=True) if phone_elem else None
                    
                    website_elem = listing.find('a', class_='track-visit-website')
                    website = website_elem.get('href') if website_elem else None
                    
                    results.append({
                        "business_name": name,
                        "address": address or city,
                        "phone": phone,
                        "website": website,
                        "has_website": bool(website),
                        "location": {"lat": 0, "lng": 0},
                        "industry": category.title(),
                        "country": extract_country(address or city),
                        "source": "yellowpages"
                    })
                except:
                    continue
    except Exception as e:
        logger.debug(f"YellowPages scrape error: {e}")
    
    return results


async def scrape_yelp(category, city):
    """Scrape Yelp public listings (FREE)"""
    results = []
    city_slug = city.lower().replace(" ", "-").replace(",", "").replace(".", "")
    category_slug = category.lower().replace(" ", "+")
    url = f"https://www.yelp.com/search?find_desc={category_slug}&find_loc={city_slug}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http:
            response = await http.get(url, headers=get_random_headers())
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find business cards
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'LocalBusiness':
                        results.append({
                            "business_name": data.get('name', ''),
                            "address": data.get('address', {}).get('streetAddress', '') + ', ' + data.get('address', {}).get('addressLocality', ''),
                            "phone": data.get('telephone'),
                            "website": data.get('url') if 'yelp.com' not in str(data.get('url', '')) else None,
                            "has_website": bool(data.get('url')) and 'yelp.com' not in str(data.get('url', '')),
                            "location": {"lat": 0, "lng": 0},
                            "industry": category.title(),
                            "country": extract_country(city),
                            "source": "yelp"
                        })
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'LocalBusiness':
                                results.append({
                                    "business_name": item.get('name', ''),
                                    "address": str(item.get('address', '')),
                                    "phone": item.get('telephone'),
                                    "website": None,
                                    "has_website": False,
                                    "location": {"lat": 0, "lng": 0},
                                    "industry": category.title(),
                                    "country": extract_country(city),
                                    "source": "yelp"
                                })
                except:
                    continue
    except Exception as e:
        logger.debug(f"Yelp scrape error: {e}")
    
    return results


async def scrape_google_search(category, city):
    """Scrape Google Search results for businesses (FREE but limited)"""
    results = []
    query = f"{category} {city} contact phone address"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=20"
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as http:
            response = await http.get(url, headers=get_random_headers())
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for local business cards
            for div in soup.find_all('div', class_=re.compile(r'.*')):
                text = div.get_text()
                if len(text) > 50 and len(text) < 500:
                    phone = extract_phone(text)
                    if phone:
                        # This might be a business listing
                        lines = text.split('\n')
                        name = lines[0][:50] if lines else None
                        if name and len(name) > 3:
                            results.append({
                                "business_name": name.strip(),
                                "address": city,
                                "phone": phone,
                                "website": None,
                                "has_website": False,
                                "location": {"lat": 0, "lng": 0},
                                "industry": category.title(),
                                "country": extract_country(city),
                                "source": "google_search"
                            })
    except Exception as e:
        logger.debug(f"Google search error: {e}")
    
    return results[:5]  # Limit results


def generate_fake_lead():
    """Generate a fake lead (1 per 10 real)"""
    names = [
        "Sunrise Bakery", "Mountain View Auto", "Coastal Cleaning Co", 
        "Urban Fitness Studio", "Green Thumb Gardens", "Swift Delivery",
        "Harmony Music School", "Elite Pet Care", "Precision Plumbing",
        "Bright Ideas Marketing", "Golden Gate Cafe", "Pacific Dental",
        "Summit Construction", "Evergreen Landscaping", "Crystal Windows"
    ]
    cities = [
        ("New York, NY", "USA"), ("Los Angeles, CA", "USA"), ("Chicago, IL", "USA"),
        ("London", "UK"), ("Toronto", "Canada"), ("Sydney", "Australia"),
        ("Berlin", "Germany"), ("Paris", "France"), ("Tokyo", "Japan"),
        ("Dubai", "UAE"), ("Singapore", "Singapore"), ("Mumbai", "India"),
        ("Mexico City", "Mexico"), ("Sao Paulo", "Brazil"), ("Cape Town", "South Africa")
    ]
    
    city, country = random.choice(cities)
    
    return {
        "id": str(uuid.uuid4()),
        "business_name": f"{random.choice(names)} {random.randint(100, 999)}",
        "address": f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Park Blvd', 'Commerce Dr'])}, {city}",
        "phone": f"+1 ({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
        "website": None,
        "has_website": False,
        "website_issues": ["No website - prime opportunity!", "Missing online presence"],
        "ai_pitch": "This business needs a website! Help them get online and grow.",
        "ai_proposal": "• Modern website\n• Google Business setup\n• Local SEO\n• Contact forms\n• Social media",
        "location": {"lat": 0, "lng": 0},
        "country": country,
        "industry": random.choice(["Restaurant", "Auto", "Salon", "Fitness", "Dental", "Retail"]),
        "source": "generated",
        "is_assigned": False,
        "is_fake": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }


async def seed_leads(target_count=10000, use_google_maps=True):
    """Main seeding function"""
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    
    current_count = await db.lead_pool.count_documents({})
    logger.info(f"Current leads: {current_count}, Target: {target_count}")
    
    if current_count >= target_count:
        logger.info("Target already reached")
        return
    
    leads_needed = target_count - current_count
    leads_added = 0
    
    categories = BUSINESS_CATEGORIES.copy()
    cities = GLOBAL_CITIES.copy()
    random.shuffle(categories)
    random.shuffle(cities)
    
    for city in cities:
        if leads_added >= leads_needed:
            break
        
        for category in random.sample(categories, min(10, len(categories))):
            if leads_added >= leads_needed:
                break
            
            logger.info(f"Searching: {category} in {city}")
            all_businesses = []
            
            # Try multiple sources
            if use_google_maps and api_key:
                businesses = await fetch_from_google_maps(category, city, api_key)
                all_businesses.extend(businesses)
                await asyncio.sleep(0.5)
            
            # Yellow Pages (FREE)
            yp_businesses = await scrape_yellowpages(category, city)
            all_businesses.extend(yp_businesses)
            await asyncio.sleep(1)
            
            # Yelp (FREE)
            yelp_businesses = await scrape_yelp(category, city)
            all_businesses.extend(yelp_businesses)
            await asyncio.sleep(1)
            
            # Process businesses
            for biz in all_businesses:
                if not biz.get("business_name"):
                    continue
                
                # Check duplicate
                exists = await db.lead_pool.find_one({
                    "business_name": biz["business_name"],
                    "address": biz["address"]
                })
                if exists:
                    continue
                
                pitch_data = get_pitch_for_business(biz)
                
                lead_doc = {
                    "id": str(uuid.uuid4()),
                    "business_name": biz["business_name"],
                    "address": biz["address"],
                    "phone": biz.get("phone"),
                    "website": biz.get("website"),
                    "has_website": biz.get("has_website", False),
                    "website_issues": pitch_data["website_issues"],
                    "ai_pitch": pitch_data["ai_pitch"],
                    "ai_proposal": pitch_data["ai_proposal"],
                    "location": biz.get("location", {"lat": 0, "lng": 0}),
                    "country": biz.get("country", "Unknown"),
                    "industry": biz.get("industry", category.title()),
                    "source": biz.get("source", "unknown"),
                    "is_assigned": False,
                    "is_fake": False,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.lead_pool.insert_one(lead_doc)
                leads_added += 1
                
                if leads_added % 100 == 0:
                    logger.info(f"Added {leads_added} leads...")
            
            await asyncio.sleep(2)  # Rate limiting
    
    # Add fake leads (1 per 10)
    fake_count = leads_added // 10
    for _ in range(fake_count):
        await db.lead_pool.insert_one(generate_fake_lead())
    
    final_count = await db.lead_pool.count_documents({})
    logger.info(f"Seeding complete! Total: {final_count}")


async def continuous_seed(interval_seconds=3600, target_increment=500):
    """Run seeding continuously"""
    logger.info(f"Starting continuous seeding every {interval_seconds} seconds")
    
    while True:
        try:
            current = await db.lead_pool.count_documents({})
            target = current + target_increment
            logger.info(f"Adding {target_increment} more leads (current: {current})")
            await seed_leads(target_count=target)
        except Exception as e:
            logger.error(f"Seeding error: {e}")
        
        logger.info(f"Sleeping for {interval_seconds} seconds...")
        await asyncio.sleep(interval_seconds)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=10000)
    parser.add_argument('--continuous', action='store_true')
    parser.add_argument('--interval', type=int, default=3600, help='Seconds between runs')
    args = parser.parse_args()
    
    # Create index
    await db.lead_pool.create_index([("business_name", 1), ("address", 1)], unique=True, sparse=True)
    
    if args.continuous:
        await continuous_seed(interval_seconds=args.interval)
    else:
        await seed_leads(target_count=args.count)


if __name__ == "__main__":
    asyncio.run(main())
