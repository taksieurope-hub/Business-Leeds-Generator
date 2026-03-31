import asyncio, uuid, httpx, re
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError

GOOGLE_API_KEY = 'AIzaSyD3vSqdoHGEwGX4NgqN6ZI3HFdOA9zf4Pg'

async def scrape_email(website, http):
    try:
        r = await http.get(website, timeout=10, follow_redirects=True)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
        excluded = ['example.com','domain.com','sentry.io','googleapis.com','schema.org','w3.org']
        for email in emails:
            if not any(ex in email.lower() for ex in excluded):
                return email
        for path in ['/contact', '/about', '/contact-us']:
            try:
                r2 = await http.get(website.rstrip('/') + path, timeout=10, follow_redirects=True)
                emails2 = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r2.text)
                for email in emails2:
                    if not any(ex in email.lower() for ex in excluded):
                        return email
            except:
                pass
    except:
        pass
    return None

def generate_email(name, website):
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
    client = AsyncIOMotorClient('mongodb+srv://gawaineelainehzmb_db_user:DfPEpULr59CY0vBF@cluster0.doxqdxt.mongodb.net/leadgen?appName=Cluster0')
    db = client['leadgen']
    count = 0
    categories = ['restaurant','hair salon','gym','dentist','electrician','bakery','cafe','lawyer','accountant','plumber','garage','pharmacy','florist','photographer','tattoo','driving school','cleaning service','pest control','catering','landscaping']
    cities = [
        'New York NY USA','Los Angeles CA USA','Chicago IL USA','Houston TX USA','Phoenix AZ USA',
        'Philadelphia PA USA','San Antonio TX USA','Dallas TX USA','Miami FL USA','Atlanta GA USA',
        'Seattle WA USA','Denver CO USA','Boston MA USA','Nashville TN USA','Portland OR USA',
        'Las Vegas NV USA','Baltimore MD USA','Louisville KY USA','Milwaukee WI USA','Albuquerque NM USA'
    ]
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as http:
        for city in cities:
            for cat in categories:
                try:
                    r = await http.get('https://maps.googleapis.com/maps/api/place/textsearch/json', params={'query': f'{cat} in {city}', 'key': GOOGLE_API_KEY})
                    data = r.json()
                    for place in data.get('results', []):
                        name = place.get('name')
                        address = place.get('formatted_address', '')
                        place_id = place.get('place_id')
                        if not name:
                            continue
                        phone = None
                        website = None
                        try:
                            d = await http.get('https://maps.googleapis.com/maps/api/place/details/json', params={'place_id': place_id, 'fields': 'formatted_phone_number,website', 'key': GOOGLE_API_KEY})
                            details = d.json().get('result', {})
                            phone = details.get('formatted_phone_number')
                            website = details.get('website')
                        except:
                            pass
                        email = None
                        if website:
                            email = await scrape_email(website, http)
                        if not email:
                            email = generate_email(name, website)
                        has_website = bool(website)
                        if has_website:
                            pitch = f'Hi, I reviewed {name}\'s website and found opportunities to improve it. A modern, faster website could increase your customer conversions by 40%.'
                        else:
                            pitch = f'Hi, I noticed {name} does not have a website. 80% of customers search online first - you could be missing hundreds of potential customers every month.'
                        try:
                            await db.lead_pool.insert_one({'id': str(uuid.uuid4()), 'business_name': name, 'address': address, 'phone': phone, 'email': email, 'website': website, 'has_website': has_website, 'ai_pitch': pitch, 'ai_proposal': 'Professional website design, mobile-optimised, Google Business setup and SEO included.', 'country': 'USA', 'industry': cat.title(), 'is_assigned': False, 'is_fake': False, 'created_at': datetime.now(timezone.utc).isoformat()})
                            count += 1
                        except DuplicateKeyError:
                            pass
                        await asyncio.sleep(0.2)
                    print(f'{cat} in {city} - Total: {count}')
                except Exception as e:
                    print(f'Error {cat} in {city}: {e}')
                await asyncio.sleep(0.5)
    print('DONE! Total leads:', await db.lead_pool.count_documents({}))

asyncio.run(seed())
