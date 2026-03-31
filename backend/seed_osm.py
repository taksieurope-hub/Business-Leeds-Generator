import asyncio, uuid, httpx
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError

async def seed():
    client = AsyncIOMotorClient('mongodb+srv://gawaineelainehzmb_db_user:DfPEpULr59CY0vBF@cluster0.doxqdxt.mongodb.net/leadgen?appName=Cluster0')
    db = client['leadgen']
    count = 0
    categories = ['restaurant','hair_salon','gym','dentist','electrician','bakery','cafe','lawyer','accountant','plumber','garage','pharmacy']
    cities = [('London',51.5074,-0.1278),('Manchester',53.4808,-2.2426),('Birmingham',52.4862,-1.8904),('Leeds',53.8008,-1.5491),('Glasgow',55.8642,-4.2518),('Liverpool',53.4084,-2.9916),('Bristol',51.4545,-2.5879),('Edinburgh',55.9533,-3.1883)]
    servers = ['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter']
    server_idx = 0
    async with httpx.AsyncClient(timeout=60) as http:
        for city_name, lat, lon in cities:
            for cat in categories:
                for attempt in range(3):
                    try:
                        server = servers[server_idx % len(servers)]
                        query = f'[out:json];node["amenity"="{cat}"](around:5000,{lat},{lon});out 20;'
                        r = await http.post(server, data=query)
                        if r.status_code != 200 or not r.text.strip():
                            server_idx += 1
                            await asyncio.sleep(20)
                            continue
                        data = r.json()
                        for el in data.get('elements', []):
                            tags = el.get('tags', {})
                            name = tags.get('name')
                            if not name:
                                continue
                            try:
                                await db.lead_pool.insert_one({'id': str(uuid.uuid4()), 'business_name': name, 'address': f'{tags.get("addr:housenumber","") } {tags.get("addr:street","High Street")}, {city_name}'.strip(), 'phone': tags.get('phone'), 'website': tags.get('website'), 'has_website': bool(tags.get('website')), 'ai_pitch': f'Hi I found {name} and noticed an opportunity to improve your online presence. 80 percent of customers search online before visiting.', 'ai_proposal': 'Professional website design mobile-optimised Google Business setup and SEO included.', 'country': 'UK', 'industry': cat.replace("_"," ").title(), 'is_assigned': False, 'is_fake': False, 'created_at': datetime.now(timezone.utc).isoformat()})
                                count += 1
                            except DuplicateKeyError:
                                pass
                        print(f'{cat} in {city_name} - Total: {count}')
                        break
                    except Exception as e:
                        print(f'Error: {e}')
                        server_idx += 1
                        await asyncio.sleep(20)
                await asyncio.sleep(5)
    print('DONE! Total leads:', await db.lead_pool.count_documents({}))

asyncio.run(seed())
