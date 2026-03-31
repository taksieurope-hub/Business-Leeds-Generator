import asyncio, uuid, httpx, re
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError

GOOGLE_API_KEY = 'AIzaSyD3vSqdoHGEwGX4NgqN6ZI3HFdOA9zf4Pg'
MONGO_URL = 'mongodb+srv://gawaineelainehzmb_db_user:DfPEpULr59CY0vBF@cluster0.doxqdxt.mongodb.net/leadgen?appName=Cluster0'

async def scrape_email(website, http):
    try:
        r = await http.get(website, timeout=10, follow_redirects=True)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        excluded = ['example.com','domain.com','sentry.io','googleapis.com','schema.org','w3.org','wixpress.com','squarespace.com']
        for email in emails:
            if not any(ex in email.lower() for ex in excluded):
                if any(p in email.lower() for p in ['info@','contact@','hello@','support@','admin@','sales@']):
                    return email
        for email in emails:
            if not any(ex in email.lower() for ex in excluded):
                return email
        for path in ['/contact', '/contact-us', '/about']:
            try:
                r2 = await http.get(website.rstrip('/') + path, timeout=8, follow_redirects=True)
                emails2 = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r2.text)
                for email in emails2:
                    if not any(ex in email.lower() for ex in excluded):
                        return email
            except:
                pass
    except:
        pass
    return None

def make_email(name, website):
    if website:
        try:
            from urllib.parse import urlparse
            domain = urlparse(website).netloc.replace('www.','')
            if domain:
                return f'info@{domain}'
        except:
            pass
    clean = re.sub(r'[^a-z0-9]', '', name.lower())[:20]
    return f'info@{clean}.com'

async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client['leadgen']
    count = 0

    categories = [
        'restaurant','hair salon','gym','dentist','electrician',
        'bakery','cafe','lawyer','accountant','plumber','garage',
        'pharmacy','florist','photographer','cleaning service',
        'pest control','driving school','tattoo','estate agent','catering'
    ]

    cities = [
        'London UK','Manchester UK','Birmingham UK','Leeds UK',
        'Glasgow UK','Liverpool UK','Bristol UK','Edinburgh UK',
        'Sheffield UK','Nottingham UK','Leicester UK','Cardiff UK',
        'New York USA','Los Angeles USA','Chicago USA','Houston USA',
        'Phoenix USA','Philadelphia USA','Dallas USA','Miami USA',
        'Atlanta USA','Seattle USA','Denver USA','Boston USA'
    ]

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as http:
        for city in cities:
            for cat in categories:
                try:
                    r = await http.get(
                        'https://maps.googleapis.com/maps/api/place/textsearch/json',
                        params={'query': f'{cat} in {city}', 'key': GOOGLE_API_KEY}
                    )
                    places = r.json().get('results', [])

                    for place in places:
                        place_id = place.get('place_id')
                        if not place_id:
                            continue

                        # Get full details
                        d = await http.get(
                            'https://maps.googleapis.com/maps/api/place/details/json',
                            params={
                                'place_id': place_id,
                                'fields': 'name,formatted_address,formatted_phone_number,website,geometry',
                                'key': GOOGLE_API_KEY
                            }
                        )
                        details = d.json().get('result', {})

                        name = details.get('name')
                        address = details.get('formatted_address', '')
                        phone = details.get('formatted_phone_number')
                        website = details.get('website')
                        lat = details.get('geometry', {}).get('location', {}).get('lat', 0)
                        lng = details.get('geometry', {}).get('location', {}).get('lng', 0)

                        if not name:
                            continue

                        # Scrape email
                        email = None
                        if website:
                            email = await scrape_email(website, http)
                        if not email:
                            email = make_email(name, website)

                        has_website = bool(website)
                        country = 'UK' if 'UK' in city else 'USA'

                        if has_website:
                            pitch = f'Hi, I reviewed {name}\'s website and found opportunities to improve it. A modern, faster website could increase your customer conversions significantly.'
                        else:
                            pitch = f'Hi, I noticed {name} does not have a website. Over 80% of customers search online before visiting - you could be missing hundreds of potential customers every month.'

                        try:
                            await db.lead_pool.insert_one({
                                'id': str(uuid.uuid4()),
                                'business_name': name,
                                'address': address,
                                'phone': phone,
                                'email': email,
                                'website': website,
                                'has_website': has_website,
                                'website_issues': ['No website - missing online customers'] if not has_website else ['Website could be improved'],
                                'ai_pitch': pitch,
                                'ai_proposal': 'Professional website design, mobile-optimised, Google Business setup and SEO included.',
                                'location': {'lat': lat, 'lng': lng},
                                'country': country,
                                'industry': cat.title(),
                                'is_assigned': False,
                                'is_fake': False,
                                'created_at': datetime.now(timezone.utc).isoformat()
                            })
                            count += 1
                        except DuplicateKeyError:
                            pass

                        await asyncio.sleep(0.2)

                    print(f'{cat} in {city} - Total so far: {count}')

                except Exception as e:
                    print(f'Error {cat} in {city}: {e}')

                await asyncio.sleep(0.5)

    print(f'DONE! Total leads added: {count}')
    print(f'Total in pool: {await db.lead_pool.count_documents({})}')

asyncio.run(seed())
