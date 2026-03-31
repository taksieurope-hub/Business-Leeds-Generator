"""
Lead Seeder - Fetches real businesses from Google Maps API
Run this script to populate the database with real business leads.
Usage: python lead_seeder.py [--count 1000]
"""

import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import httpx
import random
import uuid
from datetime import datetime, timezone
import logging
import argparse

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Business categories to search
BUSINESS_CATEGORIES = [
    "restaurant", "cafe", "bakery", "pizza", "sushi", "bar", "pub", "brewery",
    "auto repair", "car wash", "mechanic", "tire shop", "auto body shop",
    "hair salon", "barber shop", "nail salon", "spa", "beauty salon", "tattoo",
    "dentist", "doctor", "clinic", "pharmacy", "chiropractor", "optometrist",
    "gym", "fitness center", "yoga studio", "pilates", "crossfit", "martial arts",
    "plumber", "electrician", "hvac", "roofing", "landscaping", "handyman",
    "cleaning service", "maid service", "carpet cleaning", "pressure washing",
    "pet grooming", "veterinarian", "pet store", "dog training", "pet boarding",
    "florist", "gift shop", "jewelry store", "clothing store", "shoe store",
    "furniture store", "hardware store", "electronics repair", "computer repair",
    "accounting", "lawyer", "insurance", "real estate agent", "financial advisor",
    "photographer", "wedding planner", "event venue", "catering", "dj service",
    "tutoring", "music lessons", "dance studio", "art classes", "driving school",
    "daycare", "preschool", "after school program", "summer camp",
    "printing shop", "sign shop", "tailor", "dry cleaner", "laundromat",
    "locksmith", "moving company", "storage facility", "shipping store",
    "travel agency", "hotel", "motel", "bed and breakfast", "hostel",
    "construction", "contractor", "architect", "interior designer",
    "massage therapy", "acupuncture", "physical therapy", "counselor",
    "ice cream shop", "donut shop", "bagel shop", "deli", "butcher",
    "wine shop", "liquor store", "convenience store", "grocery store",
    "bookstore", "toy store", "sporting goods", "bike shop", "surf shop"
]

# Cities around the world to search
GLOBAL_CITIES = [
    # USA - Major cities
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Boston, MA",
    "Nashville, TN", "Detroit, MI", "Portland, OR", "Las Vegas, NV", "Memphis, TN",
    "Louisville, KY", "Baltimore, MD", "Milwaukee, WI", "Albuquerque, NM", "Tucson, AZ",
    "Fresno, CA", "Sacramento, CA", "Atlanta, GA", "Miami, FL", "Oakland, CA",
    "Minneapolis, MN", "Cleveland, OH", "New Orleans, LA", "Tampa, FL", "Pittsburgh, PA",
    "Cincinnati, OH", "St. Louis, MO", "Orlando, FL", "Honolulu, HI", "Anchorage, AK",
    
    # USA - Smaller cities
    "Boise, ID", "Salt Lake City, UT", "Reno, NV", "Spokane, WA", "Eugene, OR",
    "Santa Fe, NM", "Charleston, SC", "Savannah, GA", "Asheville, NC", "Burlington, VT",
    "Providence, RI", "Hartford, CT", "Buffalo, NY", "Rochester, NY", "Syracuse, NY",
    
    # Canada
    "Toronto, Ontario, Canada", "Vancouver, BC, Canada", "Montreal, Quebec, Canada",
    "Calgary, Alberta, Canada", "Edmonton, Alberta, Canada", "Ottawa, Ontario, Canada",
    "Winnipeg, Manitoba, Canada", "Quebec City, Quebec, Canada", "Hamilton, Ontario, Canada",
    "Halifax, Nova Scotia, Canada", "Victoria, BC, Canada", "Saskatoon, Saskatchewan, Canada",
    
    # UK
    "London, UK", "Manchester, UK", "Birmingham, UK", "Leeds, UK", "Glasgow, UK",
    "Liverpool, UK", "Bristol, UK", "Sheffield, UK", "Edinburgh, UK", "Cardiff, UK",
    "Belfast, UK", "Newcastle, UK", "Nottingham, UK", "Southampton, UK", "Brighton, UK",
    
    # Australia
    "Sydney, Australia", "Melbourne, Australia", "Brisbane, Australia", "Perth, Australia",
    "Adelaide, Australia", "Gold Coast, Australia", "Canberra, Australia", "Hobart, Australia",
    "Darwin, Australia", "Cairns, Australia", "Newcastle, Australia", "Wollongong, Australia",
    
    # Germany
    "Berlin, Germany", "Munich, Germany", "Hamburg, Germany", "Frankfurt, Germany",
    "Cologne, Germany", "Stuttgart, Germany", "Dusseldorf, Germany", "Leipzig, Germany",
    "Dortmund, Germany", "Essen, Germany", "Bremen, Germany", "Dresden, Germany",
    
    # France
    "Paris, France", "Lyon, France", "Marseille, France", "Toulouse, France",
    "Nice, France", "Bordeaux, France", "Lille, France", "Strasbourg, France",
    "Nantes, France", "Montpellier, France", "Rennes, France", "Grenoble, France",
    
    # Spain
    "Madrid, Spain", "Barcelona, Spain", "Valencia, Spain", "Seville, Spain",
    "Bilbao, Spain", "Malaga, Spain", "Zaragoza, Spain", "Palma, Spain",
    
    # Italy
    "Rome, Italy", "Milan, Italy", "Naples, Italy", "Turin, Italy", "Florence, Italy",
    "Bologna, Italy", "Venice, Italy", "Verona, Italy", "Genoa, Italy", "Palermo, Italy",
    
    # Netherlands
    "Amsterdam, Netherlands", "Rotterdam, Netherlands", "The Hague, Netherlands",
    "Utrecht, Netherlands", "Eindhoven, Netherlands", "Groningen, Netherlands",
    
    # Belgium
    "Brussels, Belgium", "Antwerp, Belgium", "Ghent, Belgium", "Bruges, Belgium",
    
    # Switzerland
    "Zurich, Switzerland", "Geneva, Switzerland", "Basel, Switzerland", "Bern, Switzerland",
    
    # Austria
    "Vienna, Austria", "Salzburg, Austria", "Innsbruck, Austria", "Graz, Austria",
    
    # Scandinavia
    "Stockholm, Sweden", "Gothenburg, Sweden", "Malmo, Sweden",
    "Copenhagen, Denmark", "Aarhus, Denmark",
    "Oslo, Norway", "Bergen, Norway",
    "Helsinki, Finland", "Tampere, Finland",
    
    # Ireland
    "Dublin, Ireland", "Cork, Ireland", "Galway, Ireland", "Limerick, Ireland",
    
    # Portugal
    "Lisbon, Portugal", "Porto, Portugal", "Faro, Portugal", "Braga, Portugal",
    
    # Poland
    "Warsaw, Poland", "Krakow, Poland", "Wroclaw, Poland", "Gdansk, Poland",
    
    # Czech Republic
    "Prague, Czech Republic", "Brno, Czech Republic",
    
    # Greece
    "Athens, Greece", "Thessaloniki, Greece", "Heraklion, Greece",
    
    # Japan
    "Tokyo, Japan", "Osaka, Japan", "Kyoto, Japan", "Yokohama, Japan",
    "Nagoya, Japan", "Sapporo, Japan", "Kobe, Japan", "Fukuoka, Japan",
    
    # South Korea
    "Seoul, South Korea", "Busan, South Korea", "Incheon, South Korea",
    
    # China
    "Shanghai, China", "Beijing, China", "Shenzhen, China", "Guangzhou, China",
    "Hong Kong", "Hangzhou, China", "Chengdu, China", "Xi'an, China",
    
    # Singapore
    "Singapore",
    
    # Malaysia
    "Kuala Lumpur, Malaysia", "Penang, Malaysia", "Johor Bahru, Malaysia",
    
    # Thailand
    "Bangkok, Thailand", "Chiang Mai, Thailand", "Phuket, Thailand",
    
    # Vietnam
    "Ho Chi Minh City, Vietnam", "Hanoi, Vietnam", "Da Nang, Vietnam",
    
    # Philippines
    "Manila, Philippines", "Cebu, Philippines", "Davao, Philippines",
    
    # Indonesia
    "Jakarta, Indonesia", "Bali, Indonesia", "Surabaya, Indonesia",
    
    # India
    "Mumbai, India", "Delhi, India", "Bangalore, India", "Chennai, India",
    "Kolkata, India", "Hyderabad, India", "Pune, India", "Ahmedabad, India",
    "Jaipur, India", "Goa, India", "Kochi, India", "Chandigarh, India",
    
    # UAE
    "Dubai, UAE", "Abu Dhabi, UAE", "Sharjah, UAE",
    
    # Saudi Arabia
    "Riyadh, Saudi Arabia", "Jeddah, Saudi Arabia", "Dammam, Saudi Arabia",
    
    # Israel
    "Tel Aviv, Israel", "Jerusalem, Israel", "Haifa, Israel",
    
    # Turkey
    "Istanbul, Turkey", "Ankara, Turkey", "Izmir, Turkey", "Antalya, Turkey",
    
    # South Africa
    "Johannesburg, South Africa", "Cape Town, South Africa", "Durban, South Africa",
    "Pretoria, South Africa", "Port Elizabeth, South Africa",
    
    # Egypt
    "Cairo, Egypt", "Alexandria, Egypt",
    
    # Morocco
    "Casablanca, Morocco", "Marrakech, Morocco", "Fes, Morocco",
    
    # Nigeria
    "Lagos, Nigeria", "Abuja, Nigeria",
    
    # Kenya
    "Nairobi, Kenya", "Mombasa, Kenya",
    
    # Brazil
    "Sao Paulo, Brazil", "Rio de Janeiro, Brazil", "Brasilia, Brazil",
    "Salvador, Brazil", "Fortaleza, Brazil", "Belo Horizonte, Brazil",
    "Curitiba, Brazil", "Porto Alegre, Brazil", "Recife, Brazil",
    
    # Argentina
    "Buenos Aires, Argentina", "Cordoba, Argentina", "Rosario, Argentina",
    
    # Chile
    "Santiago, Chile", "Valparaiso, Chile", "Concepcion, Chile",
    
    # Colombia
    "Bogota, Colombia", "Medellin, Colombia", "Cali, Colombia", "Cartagena, Colombia",
    
    # Mexico
    "Mexico City, Mexico", "Guadalajara, Mexico", "Monterrey, Mexico",
    "Cancun, Mexico", "Tijuana, Mexico", "Puebla, Mexico", "Merida, Mexico",
    
    # Peru
    "Lima, Peru", "Cusco, Peru", "Arequipa, Peru",
    
    # New Zealand
    "Auckland, New Zealand", "Wellington, New Zealand", "Christchurch, New Zealand",
]

async def fetch_businesses_from_google(query: str, location: str, api_key: str) -> list:
    """Fetch businesses from Google Maps Places API"""
    search_query = f"{query} in {location}"
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": search_query,
        "key": api_key
    }
    
    results = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(url, params=params)
            data = response.json()
            
            if data.get("status") != "OK":
                return []
            
            for place in data.get("results", [])[:20]:
                place_id = place.get("place_id")
                
                # Get detailed info
                details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                details_params = {
                    "place_id": place_id,
                    "fields": "name,formatted_address,formatted_phone_number,website,geometry,types",
                    "key": api_key
                }
                
                try:
                    details_response = await http_client.get(details_url, params=details_params)
                    details = details_response.json().get("result", {})
                    
                    # Determine country from address
                    address = details.get("formatted_address", place.get("formatted_address", ""))
                    country = extract_country(address)
                    
                    results.append({
                        "business_name": details.get("name", place.get("name", "Unknown")),
                        "address": address,
                        "phone": details.get("formatted_phone_number"),
                        "website": details.get("website"),
                        "has_website": bool(details.get("website")),
                        "location": {
                            "lat": place.get("geometry", {}).get("location", {}).get("lat", 0),
                            "lng": place.get("geometry", {}).get("location", {}).get("lng", 0)
                        },
                        "industry": query.title(),
                        "country": country,
                        "source": "google_maps"
                    })
                except Exception as e:
                    logger.warning(f"Failed to get details for place: {e}")
                    continue
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            
            # Check for next page
            next_page_token = data.get("next_page_token")
            if next_page_token:
                await asyncio.sleep(2)  # Required delay for next page token
                params["pagetoken"] = next_page_token
                try:
                    response = await http_client.get(url, params=params)
                    data = response.json()
                    for place in data.get("results", [])[:10]:
                        results.append({
                            "business_name": place.get("name", "Unknown"),
                            "address": place.get("formatted_address", ""),
                            "phone": None,
                            "website": None,
                            "has_website": False,
                            "location": {
                                "lat": place.get("geometry", {}).get("location", {}).get("lat", 0),
                                "lng": place.get("geometry", {}).get("location", {}).get("lng", 0)
                            },
                            "industry": query.title(),
                            "country": extract_country(place.get("formatted_address", "")),
                            "source": "google_maps"
                        })
                except:
                    pass
                    
    except Exception as e:
        logger.error(f"Google Maps API error for {query} in {location}: {e}")
    
    return results

def extract_country(address: str) -> str:
    """Extract country from address string"""
    address_lower = address.lower()
    
    country_mappings = {
        "usa": "USA", "united states": "USA", ", us": "USA", "u.s.": "USA",
        "canada": "Canada", ", ca ": "Canada",
        "uk": "UK", "united kingdom": "UK", "england": "UK", "scotland": "UK", "wales": "UK",
        "australia": "Australia",
        "germany": "Germany", "deutschland": "Germany",
        "france": "France",
        "spain": "Spain", "españa": "Spain",
        "italy": "Italy", "italia": "Italy",
        "netherlands": "Netherlands", "nederland": "Netherlands",
        "belgium": "Belgium",
        "switzerland": "Switzerland",
        "austria": "Austria",
        "sweden": "Sweden",
        "norway": "Norway",
        "denmark": "Denmark",
        "finland": "Finland",
        "ireland": "Ireland",
        "portugal": "Portugal",
        "poland": "Poland",
        "czech": "Czech Republic",
        "greece": "Greece",
        "japan": "Japan",
        "south korea": "South Korea", "korea": "South Korea",
        "china": "China",
        "hong kong": "Hong Kong",
        "singapore": "Singapore",
        "malaysia": "Malaysia",
        "thailand": "Thailand",
        "vietnam": "Vietnam",
        "philippines": "Philippines",
        "indonesia": "Indonesia",
        "india": "India",
        "uae": "UAE", "dubai": "UAE", "abu dhabi": "UAE",
        "saudi": "Saudi Arabia",
        "israel": "Israel",
        "turkey": "Turkey",
        "south africa": "South Africa",
        "egypt": "Egypt",
        "morocco": "Morocco",
        "nigeria": "Nigeria",
        "kenya": "Kenya",
        "brazil": "Brazil", "brasil": "Brazil",
        "argentina": "Argentina",
        "chile": "Chile",
        "colombia": "Colombia",
        "mexico": "Mexico", "méxico": "Mexico",
        "peru": "Peru",
        "new zealand": "New Zealand",
    }
    
    for key, value in country_mappings.items():
        if key in address_lower:
            return value
    
    return "Unknown"

def get_pitch_for_business(business: dict) -> dict:
    """Generate pitch and proposal for a business"""
    has_website = business.get("has_website", False)
    industry = business.get("industry", "General")
    business_name = business.get("business_name", "This business")
    country = business.get("country", "your area")
    
    if not has_website:
        pitches = [
            f"I noticed {business_name} doesn't have a website yet. In today's digital world, over 80% of customers search online before visiting a business. A professional website could help you reach hundreds of new customers in {country}.",
            f"Hi! I came across {business_name} and noticed you're missing out on online customers. A modern website for your {industry.lower()} business could increase your visibility and bring in 30-50% more customers.",
            f"{business_name} could benefit greatly from an online presence. Your competitors likely have websites - let's make sure potential customers can find YOU when they search for {industry.lower()} services.",
            f"Looking at {business_name}, I see a huge opportunity. Without a website, you're invisible to the 4.5 billion internet users worldwide. Let me help change that.",
            f"I specialize in helping {industry.lower()} businesses like {business_name} get online. A website is your 24/7 salesperson - let's build yours.",
        ]
        
        proposals = [
            f"• Create a professional, mobile-responsive website for {business_name}\n• Set up Google Business Profile optimization\n• Implement local SEO for {country}\n• Add online booking/contact forms\n• Social media integration\n• Estimated timeline: 2-3 weeks",
            f"• Design custom website showcasing your {industry.lower()} services\n• Mobile-first responsive design\n• Contact forms and click-to-call functionality\n• Google Maps integration showing your location\n• Basic SEO setup to rank in local searches\n• Optional: Online appointment scheduling",
            f"• Modern website design tailored for {industry}\n• Fast-loading, SEO-optimized pages\n• Customer testimonial section\n• Service/menu pages with pricing\n• Integration with social media\n• Analytics dashboard to track visitors",
        ]
        
        issues = [
            "No website - missing 80% of potential online customers",
            "Cannot be found in Google searches",
            "No online presence compared to competitors",
            "Missing opportunities for online bookings/inquiries",
            "No way for customers to find business hours or contact info online"
        ]
    else:
        pitches = [
            f"I reviewed {business_name}'s website and found several opportunities for improvement. Modern website standards have changed significantly - an updated design could improve your conversion rate by 40%.",
            f"Your current website may be losing potential customers due to outdated design patterns. I'd love to help modernize it and improve your online presence.",
            f"{business_name}'s website could use a refresh! Mobile users make up 60% of web traffic now, and an optimized site could significantly boost your {industry.lower()} business.",
            f"I analyzed your website and found it could perform much better. Simple improvements could double your leads and customer inquiries.",
        ]
        
        proposals = [
            f"• Website redesign with modern aesthetics\n• Mobile responsiveness optimization\n• Page speed improvements (affects Google ranking)\n• SEO audit and optimization\n• Updated contact/booking system\n• Security updates (SSL, etc.)",
            f"• Full website audit and UX improvement\n• Modern, clean design refresh\n• Mobile optimization for all devices\n• Improved call-to-action buttons\n• Integration with current marketing tools\n• Performance optimization",
        ]
        
        issues = [
            "Website may not be mobile-friendly",
            "Potentially outdated design patterns",
            "Page speed optimization needed",
            "SEO improvements recommended",
            "Modern UX standards not met"
        ]
    
    return {
        "ai_pitch": random.choice(pitches),
        "ai_proposal": random.choice(proposals),
        "website_issues": issues
    }

async def seed_leads(target_count: int = 10000):
    """Main function to seed leads from Google Maps"""
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not set")
        return
    
    # Get current lead count
    current_count = await db.lead_pool.count_documents({})
    logger.info(f"Current leads in pool: {current_count}")
    
    if current_count >= target_count:
        logger.info(f"Target of {target_count} already reached")
        return
    
    leads_needed = target_count - current_count
    leads_added = 0
    
    # Shuffle categories and cities for variety
    categories = BUSINESS_CATEGORIES.copy()
    cities = GLOBAL_CITIES.copy()
    random.shuffle(categories)
    random.shuffle(cities)
    
    for city in cities:
        if leads_added >= leads_needed:
            break
            
        for category in categories:
            if leads_added >= leads_needed:
                break
            
            logger.info(f"Searching: {category} in {city}")
            businesses = await fetch_businesses_from_google(category, city, api_key)
            
            for business in businesses:
                # Check if already exists
                existing = await db.lead_pool.find_one({
                    "business_name": business["business_name"],
                    "address": business["address"]
                })
                
                if existing:
                    continue
                
                # Add pitch data
                pitch_data = get_pitch_for_business(business)
                
                lead_doc = {
                    "id": str(uuid.uuid4()),
                    "business_name": business["business_name"],
                    "address": business["address"],
                    "phone": business.get("phone"),
                    "website": business.get("website"),
                    "has_website": business.get("has_website", False),
                    "website_issues": pitch_data["website_issues"],
                    "ai_pitch": pitch_data["ai_pitch"],
                    "ai_proposal": pitch_data["ai_proposal"],
                    "location": business.get("location", {"lat": 0, "lng": 0}),
                    "country": business.get("country", "Unknown"),
                    "industry": business.get("industry", category.title()),
                    "source": business.get("source", "google_maps"),
                    "is_assigned": False,
                    "is_fake": False,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.lead_pool.insert_one(lead_doc)
                leads_added += 1
                
                if leads_added % 100 == 0:
                    logger.info(f"Added {leads_added} leads so far...")
            
            # Delay between categories to avoid rate limiting
            await asyncio.sleep(1)
        
        # Delay between cities
        await asyncio.sleep(2)
    
    # Add fake leads (1 per 10 real)
    fake_count = leads_added // 10
    for _ in range(fake_count):
        fake_lead = generate_fake_lead()
        await db.lead_pool.insert_one(fake_lead)
    
    final_count = await db.lead_pool.count_documents({})
    logger.info(f"Seeding complete! Total leads in pool: {final_count}")

def generate_fake_lead() -> dict:
    """Generate a fake lead for padding"""
    fake_names = [
        "Sunrise Bakery", "Mountain View Auto", "Coastal Cleaning Co", 
        "Urban Fitness Studio", "Green Thumb Gardens", "Swift Delivery Services",
        "Harmony Music School", "Elite Pet Care", "Precision Plumbing",
        "Bright Ideas Marketing", "Golden Gate Cafe", "Pacific Dental",
        "Summit Construction", "Evergreen Landscaping", "Crystal Clear Windows"
    ]
    fake_cities = [
        ("New York, NY", "USA"), ("Los Angeles, CA", "USA"), ("Chicago, IL", "USA"),
        ("London", "UK"), ("Toronto, Ontario", "Canada"), ("Sydney", "Australia"),
        ("Berlin", "Germany"), ("Paris", "France"), ("Tokyo", "Japan"),
        ("Dubai", "UAE"), ("Singapore", "Singapore"), ("Mumbai", "India")
    ]
    
    city, country = random.choice(fake_cities)
    
    return {
        "id": str(uuid.uuid4()),
        "business_name": f"{random.choice(fake_names)} {random.randint(100, 999)}",
        "address": f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Park Blvd', 'Commerce Dr', 'Market St'])}, {city}",
        "phone": f"+1 ({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
        "website": None,
        "has_website": False,
        "website_issues": ["No website exists - prime opportunity!", "Missing online presence", "No Google visibility"],
        "ai_pitch": "This business has no online presence! Help them establish a professional website to reach more customers and grow their business. This is a prime opportunity.",
        "ai_proposal": "• Create a modern, mobile-responsive website\n• Set up Google Business Profile\n• Implement local SEO\n• Add contact forms and booking system\n• Social media integration\n• Analytics setup",
        "location": {"lat": 0, "lng": 0},
        "country": country,
        "industry": random.choice(["Restaurant", "Auto Repair", "Salon", "Fitness", "Dental", "Retail"]),
        "source": "generated",
        "is_assigned": False,
        "is_fake": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

async def main():
    parser = argparse.ArgumentParser(description='Seed lead database from Google Maps')
    parser.add_argument('--count', type=int, default=10000, help='Target number of leads')
    args = parser.parse_args()
    
    logger.info(f"Starting lead seeder with target: {args.count} leads")
    await seed_leads(args.count)

if __name__ == "__main__":
    asyncio.run(main())
