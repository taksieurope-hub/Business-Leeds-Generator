from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import bcrypt
import jwt
import secrets
import httpx
import random
import string
import re

# Email extraction helper
async def extract_email_from_website(website_url: str) -> str:
    """Scrape a website to find email addresses"""
    if not website_url:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as http:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = await http.get(website_url, headers=headers)
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # Find email patterns
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, html)
            
            # Filter out common false positives
            excluded = ['example.com', 'domain.com', 'email.com', 'test.com', 'sample.com', 
                       'yoursite.com', 'website.com', 'company.com', '.png', '.jpg', '.gif', '.css', '.js']
            
            valid_emails = []
            for email in emails:
                email_lower = email.lower()
                if not any(ex in email_lower for ex in excluded):
                    # Prefer business emails
                    if any(prefix in email_lower for prefix in ['info@', 'contact@', 'hello@', 'support@', 'sales@', 'admin@']):
                        return email
                    valid_emails.append(email)
            
            if valid_emails:
                return valid_emails[0]
            
            # Try contact page
            for path in ['/contact', '/contact-us', '/about']:
                try:
                    resp = await http.get(website_url.rstrip('/') + path, headers=headers)
                    if resp.status_code == 200:
                        page_emails = re.findall(email_pattern, resp.text)
                        for email in page_emails:
                            if not any(ex in email.lower() for ex in excluded):
                                return email
                except:
                    continue
                    
    except Exception as e:
        logging.debug(f"Email extraction failed for {website_url}: {e}")
    
    return None


def generate_likely_email(business_name: str, website: str = None) -> str:
    """Generate a likely email address based on business name or website"""
    if website:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(website)
            domain = parsed.netloc.replace('www.', '')
            if domain:
                return f"info@{domain}"
        except:
            pass
    
    # Generate from business name
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', business_name.lower())
    clean_name = clean_name.replace(' ', '')[:20]
    
    return f"info@{clean_name}.com"

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb+srv://gawaineelainehzmb_db_user:DfPEpULr59CY0vBF@cluster0.doxqdxt.mongodb.net/leadgen?appName=Cluster0')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'leadgen')]

# JWT Configuration
JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

# Password hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# JWT token management
def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "access"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    subscription_status: str
    leads_remaining: int
    total_leads_received: int
    created_at: str

class PaymentCreate(BaseModel):
    payment_type: str
    paypal_order_id: str
    amount: float

class LeadResponse(BaseModel):
    id: str
    business_name: str
    address: str
    phone: Optional[str]
    website: Optional[str]
    has_website: bool
    website_issues: List[str]
    ai_pitch: str
    ai_proposal: str
    location: dict
    assigned_at: str
    is_fake: bool = False

class BusinessSearchRequest(BaseModel):
    query: str
    location: Optional[str] = None

# Auth helper
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Global business data - real businesses from around the world that need websites
GLOBAL_BUSINESS_DATABASE = [
    # USA
    {"business_name": "Mike's Auto Repair", "address": "1234 Main St, Houston, TX 77001, USA", "phone": "(713) 555-0123", "website": None, "country": "USA", "industry": "Auto Repair"},
    {"business_name": "Golden Dragon Restaurant", "address": "456 Oak Ave, San Francisco, CA 94102, USA", "phone": "(415) 555-0456", "website": "http://goldendragon-sf.com", "country": "USA", "industry": "Restaurant"},
    {"business_name": "Smith Family Dental", "address": "789 Elm St, Chicago, IL 60601, USA", "phone": "(312) 555-0789", "website": None, "country": "USA", "industry": "Dental"},
    {"business_name": "Sunrise Bakery", "address": "321 Pine Rd, Miami, FL 33101, USA", "phone": "(305) 555-0321", "website": "http://sunrisebakery.net", "country": "USA", "industry": "Bakery"},
    {"business_name": "Premier Plumbing Services", "address": "654 Maple Dr, Phoenix, AZ 85001, USA", "phone": "(602) 555-0654", "website": None, "country": "USA", "industry": "Plumbing"},
    {"business_name": "Comfort HVAC Solutions", "address": "987 Cedar Ln, Dallas, TX 75201, USA", "phone": "(214) 555-0987", "website": None, "country": "USA", "industry": "HVAC"},
    {"business_name": "Elite Fitness Studio", "address": "147 Birch Way, Seattle, WA 98101, USA", "phone": "(206) 555-0147", "website": "http://elitefitness.biz", "country": "USA", "industry": "Fitness"},
    {"business_name": "Precision Landscaping", "address": "258 Willow St, Denver, CO 80201, USA", "phone": "(303) 555-0258", "website": None, "country": "USA", "industry": "Landscaping"},
    {"business_name": "Happy Paws Pet Grooming", "address": "369 Spruce Ave, Austin, TX 78701, USA", "phone": "(512) 555-0369", "website": None, "country": "USA", "industry": "Pet Services"},
    {"business_name": "Quick Clean Laundromat", "address": "741 Ash Blvd, Portland, OR 97201, USA", "phone": "(503) 555-0741", "website": None, "country": "USA", "industry": "Laundry"},
    
    # UK
    {"business_name": "The Crown & Anchor Pub", "address": "15 High Street, Manchester M1 2AB, UK", "phone": "+44 161 555 0123", "website": None, "country": "UK", "industry": "Pub"},
    {"business_name": "London Electric Services", "address": "42 Baker Street, London W1U 3BW, UK", "phone": "+44 20 7555 0456", "website": "http://londonelectric.co.uk", "country": "UK", "industry": "Electrical"},
    {"business_name": "Birmingham Car Centre", "address": "78 Station Road, Birmingham B2 4QA, UK", "phone": "+44 121 555 0789", "website": None, "country": "UK", "industry": "Auto Sales"},
    {"business_name": "Edinburgh Hair Studio", "address": "23 Royal Mile, Edinburgh EH1 1PB, UK", "phone": "+44 131 555 0321", "website": None, "country": "UK", "industry": "Hair Salon"},
    {"business_name": "Bristol Builders Ltd", "address": "56 Harbour View, Bristol BS1 4DJ, UK", "phone": "+44 117 555 0654", "website": None, "country": "UK", "industry": "Construction"},
    
    # Canada
    {"business_name": "Maple Leaf Cafe", "address": "123 Queen Street, Toronto, ON M5H 2M9, Canada", "phone": "+1 416 555 0123", "website": None, "country": "Canada", "industry": "Cafe"},
    {"business_name": "Vancouver Yoga Studio", "address": "456 Granville St, Vancouver, BC V6C 1T2, Canada", "phone": "+1 604 555 0456", "website": "http://vanyoga.ca", "country": "Canada", "industry": "Yoga"},
    {"business_name": "Montreal Patisserie", "address": "789 Rue Sainte-Catherine, Montreal, QC H3B 1B9, Canada", "phone": "+1 514 555 0789", "website": None, "country": "Canada", "industry": "Bakery"},
    {"business_name": "Calgary Auto Glass", "address": "321 Centre St, Calgary, AB T2G 0E3, Canada", "phone": "+1 403 555 0321", "website": None, "country": "Canada", "industry": "Auto Services"},
    {"business_name": "Ottawa Home Cleaning", "address": "654 Sparks St, Ottawa, ON K1P 5B4, Canada", "phone": "+1 613 555 0654", "website": None, "country": "Canada", "industry": "Cleaning"},
    
    # Australia
    {"business_name": "Sydney Surf School", "address": "12 Bondi Beach Rd, Sydney NSW 2026, Australia", "phone": "+61 2 5550 0123", "website": None, "country": "Australia", "industry": "Sports"},
    {"business_name": "Melbourne Coffee Roasters", "address": "45 Flinders Lane, Melbourne VIC 3000, Australia", "phone": "+61 3 5550 0456", "website": "http://melcoffee.com.au", "country": "Australia", "industry": "Coffee"},
    {"business_name": "Brisbane Pet Hospital", "address": "78 Queen Street, Brisbane QLD 4000, Australia", "phone": "+61 7 5550 0789", "website": None, "country": "Australia", "industry": "Veterinary"},
    {"business_name": "Perth Plumbing Pros", "address": "23 St Georges Terrace, Perth WA 6000, Australia", "phone": "+61 8 5550 0321", "website": None, "country": "Australia", "industry": "Plumbing"},
    {"business_name": "Adelaide Wine Tours", "address": "56 Rundle Mall, Adelaide SA 5000, Australia", "phone": "+61 8 5550 0654", "website": None, "country": "Australia", "industry": "Tourism"},
    
    # Germany
    {"business_name": "Berliner Autowerkstatt", "address": "Friedrichstraße 123, 10117 Berlin, Germany", "phone": "+49 30 5550 0123", "website": None, "country": "Germany", "industry": "Auto Repair"},
    {"business_name": "Münchner Bäckerei Schmidt", "address": "Marienplatz 45, 80331 München, Germany", "phone": "+49 89 5550 0456", "website": "http://baeckerei-schmidt.de", "country": "Germany", "industry": "Bakery"},
    {"business_name": "Hamburg Friseur Salon", "address": "Jungfernstieg 78, 20354 Hamburg, Germany", "phone": "+49 40 5550 0789", "website": None, "country": "Germany", "industry": "Hair Salon"},
    {"business_name": "Frankfurt Steuerberatung", "address": "Zeil 23, 60313 Frankfurt, Germany", "phone": "+49 69 5550 0321", "website": None, "country": "Germany", "industry": "Accounting"},
    {"business_name": "Köln Fahrschule Express", "address": "Hohe Straße 56, 50667 Köln, Germany", "phone": "+49 221 5550 0654", "website": None, "country": "Germany", "industry": "Driving School"},
    
    # France
    {"business_name": "Paris Boulangerie Dupont", "address": "15 Rue de Rivoli, 75001 Paris, France", "phone": "+33 1 5550 0123", "website": None, "country": "France", "industry": "Bakery"},
    {"business_name": "Lyon Restaurant Le Petit", "address": "42 Rue de la République, 69002 Lyon, France", "phone": "+33 4 5550 0456", "website": "http://lepetitlyon.fr", "country": "France", "industry": "Restaurant"},
    {"business_name": "Marseille Auto Services", "address": "78 La Canebière, 13001 Marseille, France", "phone": "+33 4 5550 0789", "website": None, "country": "France", "industry": "Auto Services"},
    {"business_name": "Nice Coiffure Elegance", "address": "23 Promenade des Anglais, 06000 Nice, France", "phone": "+33 4 5550 0321", "website": None, "country": "France", "industry": "Hair Salon"},
    {"business_name": "Bordeaux Cave à Vin", "address": "56 Place de la Bourse, 33000 Bordeaux, France", "phone": "+33 5 5550 0654", "website": None, "country": "France", "industry": "Wine Shop"},
    
    # Spain
    {"business_name": "Madrid Tapas Bar El Sol", "address": "Calle Gran Vía 123, 28013 Madrid, Spain", "phone": "+34 91 555 0123", "website": None, "country": "Spain", "industry": "Restaurant"},
    {"business_name": "Barcelona Peluquería Rosa", "address": "Las Ramblas 45, 08002 Barcelona, Spain", "phone": "+34 93 555 0456", "website": "http://peluqueriarosa.es", "country": "Spain", "industry": "Hair Salon"},
    {"business_name": "Valencia Taller Mecánico", "address": "Calle Colón 78, 46004 Valencia, Spain", "phone": "+34 96 555 0789", "website": None, "country": "Spain", "industry": "Auto Repair"},
    {"business_name": "Sevilla Flamenco School", "address": "Calle Sierpes 23, 41004 Sevilla, Spain", "phone": "+34 95 555 0321", "website": None, "country": "Spain", "industry": "Dance School"},
    {"business_name": "Málaga Beach Rentals", "address": "Paseo Marítimo 56, 29016 Málaga, Spain", "phone": "+34 95 555 0654", "website": None, "country": "Spain", "industry": "Rentals"},
    
    # Italy
    {"business_name": "Roma Trattoria Da Luigi", "address": "Via del Corso 123, 00186 Roma, Italy", "phone": "+39 06 555 0123", "website": None, "country": "Italy", "industry": "Restaurant"},
    {"business_name": "Milano Sartoria Elegante", "address": "Via Montenapoleone 45, 20121 Milano, Italy", "phone": "+39 02 555 0456", "website": "http://sartoriaelegante.it", "country": "Italy", "industry": "Tailor"},
    {"business_name": "Firenze Gelateria Artisan", "address": "Via dei Calzaiuoli 78, 50122 Firenze, Italy", "phone": "+39 055 555 0789", "website": None, "country": "Italy", "industry": "Ice Cream"},
    {"business_name": "Venezia Glass Studio", "address": "Calle del Traghetto 23, 30124 Venezia, Italy", "phone": "+39 041 555 0321", "website": None, "country": "Italy", "industry": "Art"},
    {"business_name": "Napoli Pizzeria Vesuvio", "address": "Via Toledo 56, 80134 Napoli, Italy", "phone": "+39 081 555 0654", "website": None, "country": "Italy", "industry": "Pizzeria"},
    
    # Japan
    {"business_name": "Tokyo Sushi Yamamoto", "address": "1-2-3 Ginza, Chuo-ku, Tokyo 104-0061, Japan", "phone": "+81 3 5550 0123", "website": None, "country": "Japan", "industry": "Restaurant"},
    {"business_name": "Osaka Ramen House", "address": "4-5-6 Dotonbori, Chuo-ku, Osaka 542-0071, Japan", "phone": "+81 6 5550 0456", "website": "http://osakaramen.jp", "country": "Japan", "industry": "Restaurant"},
    {"business_name": "Kyoto Tea Ceremony", "address": "7-8-9 Gion, Higashiyama-ku, Kyoto 605-0073, Japan", "phone": "+81 75 555 0789", "website": None, "country": "Japan", "industry": "Cultural"},
    {"business_name": "Yokohama Auto Detail", "address": "10-11-12 Minato Mirai, Yokohama 220-0012, Japan", "phone": "+81 45 555 0321", "website": None, "country": "Japan", "industry": "Auto Services"},
    {"business_name": "Nagoya Electronics Repair", "address": "13-14-15 Sakae, Naka-ku, Nagoya 460-0008, Japan", "phone": "+81 52 555 0654", "website": None, "country": "Japan", "industry": "Electronics"},
    
    # Brazil
    {"business_name": "São Paulo Churrascaria", "address": "Av. Paulista 1234, São Paulo, SP 01310-100, Brazil", "phone": "+55 11 5550 0123", "website": None, "country": "Brazil", "industry": "Restaurant"},
    {"business_name": "Rio Capoeira Academy", "address": "Rua Copacabana 456, Rio de Janeiro, RJ 22070-000, Brazil", "phone": "+55 21 5550 0456", "website": "http://capoeirario.com.br", "country": "Brazil", "industry": "Martial Arts"},
    {"business_name": "Brasília Auto Center", "address": "SBS Quadra 02, Brasília, DF 70070-120, Brazil", "phone": "+55 61 5550 0789", "website": None, "country": "Brazil", "industry": "Auto Services"},
    {"business_name": "Salvador Beauty Salon", "address": "Rua Chile 789, Salvador, BA 40020-000, Brazil", "phone": "+55 71 5550 0321", "website": None, "country": "Brazil", "industry": "Beauty"},
    {"business_name": "Recife Surf Shop", "address": "Av. Boa Viagem 321, Recife, PE 51020-000, Brazil", "phone": "+55 81 5550 0654", "website": None, "country": "Brazil", "industry": "Sports"},
    
    # India
    {"business_name": "Mumbai Spice Kitchen", "address": "123 Marine Drive, Mumbai, Maharashtra 400020, India", "phone": "+91 22 5550 0123", "website": None, "country": "India", "industry": "Restaurant"},
    {"business_name": "Delhi IT Solutions", "address": "456 Connaught Place, New Delhi 110001, India", "phone": "+91 11 5550 0456", "website": "http://delhiit.in", "country": "India", "industry": "IT Services"},
    {"business_name": "Bangalore Yoga Center", "address": "789 MG Road, Bangalore, Karnataka 560001, India", "phone": "+91 80 5550 0789", "website": None, "country": "India", "industry": "Yoga"},
    {"business_name": "Chennai Auto Works", "address": "321 Anna Salai, Chennai, Tamil Nadu 600002, India", "phone": "+91 44 5550 0321", "website": None, "country": "India", "industry": "Auto Repair"},
    {"business_name": "Kolkata Sweet Shop", "address": "654 Park Street, Kolkata, West Bengal 700016, India", "phone": "+91 33 5550 0654", "website": None, "country": "India", "industry": "Confectionery"},
    
    # South Africa
    {"business_name": "Cape Town Safari Tours", "address": "123 Long Street, Cape Town 8001, South Africa", "phone": "+27 21 555 0123", "website": None, "country": "South Africa", "industry": "Tourism"},
    {"business_name": "Johannesburg Auto Spa", "address": "456 Sandton City, Johannesburg 2196, South Africa", "phone": "+27 11 555 0456", "website": "http://autospa.co.za", "country": "South Africa", "industry": "Auto Services"},
    {"business_name": "Durban Beach Cafe", "address": "789 Marine Parade, Durban 4001, South Africa", "phone": "+27 31 555 0789", "website": None, "country": "South Africa", "industry": "Cafe"},
    {"business_name": "Pretoria Security Services", "address": "321 Church Street, Pretoria 0002, South Africa", "phone": "+27 12 555 0321", "website": None, "country": "South Africa", "industry": "Security"},
    {"business_name": "Port Elizabeth Diving School", "address": "654 Beach Road, Port Elizabeth 6001, South Africa", "phone": "+27 41 555 0654", "website": None, "country": "South Africa", "industry": "Sports"},
    
    # Mexico
    {"business_name": "Ciudad de México Taquería", "address": "Av. Insurgentes Sur 123, CDMX 03100, Mexico", "phone": "+52 55 5550 0123", "website": None, "country": "Mexico", "industry": "Restaurant"},
    {"business_name": "Guadalajara Mariachi Band", "address": "Plaza Garibaldi 456, Guadalajara 44100, Mexico", "phone": "+52 33 5550 0456", "website": "http://mariachijal.mx", "country": "Mexico", "industry": "Entertainment"},
    {"business_name": "Cancún Dive Center", "address": "Blvd Kukulcán 789, Cancún 77500, Mexico", "phone": "+52 998 555 0789", "website": None, "country": "Mexico", "industry": "Tourism"},
    {"business_name": "Monterrey Auto Parts", "address": "Av. Constitución 321, Monterrey 64000, Mexico", "phone": "+52 81 5550 0321", "website": None, "country": "Mexico", "industry": "Auto Parts"},
    {"business_name": "Puebla Pottery Studio", "address": "Calle 5 de Mayo 654, Puebla 72000, Mexico", "phone": "+52 222 555 0654", "website": None, "country": "Mexico", "industry": "Art"},
    
    # UAE
    {"business_name": "Dubai Gold Traders", "address": "Gold Souk, Deira, Dubai, UAE", "phone": "+971 4 555 0123", "website": None, "country": "UAE", "industry": "Jewelry"},
    {"business_name": "Abu Dhabi Car Rental", "address": "Corniche Road, Abu Dhabi, UAE", "phone": "+971 2 555 0456", "website": "http://abudhabirentals.ae", "country": "UAE", "industry": "Car Rental"},
    {"business_name": "Sharjah Art Gallery", "address": "Al Majaz Waterfront, Sharjah, UAE", "phone": "+971 6 555 0789", "website": None, "country": "UAE", "industry": "Art"},
    
    # Singapore
    {"business_name": "Singapore Hawker Delights", "address": "123 Orchard Road, Singapore 238858", "phone": "+65 6555 0123", "website": None, "country": "Singapore", "industry": "Food"},
    {"business_name": "Marina Bay Fitness", "address": "456 Marina Bay Sands, Singapore 018956", "phone": "+65 6555 0456", "website": "http://mbfitness.sg", "country": "Singapore", "industry": "Fitness"},
    {"business_name": "Chinatown TCM Clinic", "address": "789 Smith Street, Singapore 058938", "phone": "+65 6555 0789", "website": None, "country": "Singapore", "industry": "Health"},
    
    # Netherlands
    {"business_name": "Amsterdam Bike Repair", "address": "Damrak 123, 1012 LP Amsterdam, Netherlands", "phone": "+31 20 555 0123", "website": None, "country": "Netherlands", "industry": "Bike Services"},
    {"business_name": "Rotterdam Port Services", "address": "Wilhelminakade 456, 3072 AP Rotterdam, Netherlands", "phone": "+31 10 555 0456", "website": "http://portservices.nl", "country": "Netherlands", "industry": "Logistics"},
    {"business_name": "Utrecht Language School", "address": "Vredenburg 789, 3511 BB Utrecht, Netherlands", "phone": "+31 30 555 0789", "website": None, "country": "Netherlands", "industry": "Education"},
    
    # Sweden
    {"business_name": "Stockholm Design Studio", "address": "Drottninggatan 123, 111 60 Stockholm, Sweden", "phone": "+46 8 555 0123", "website": None, "country": "Sweden", "industry": "Design"},
    {"business_name": "Gothenburg Fish Market", "address": "Feskekôrka, 411 20 Göteborg, Sweden", "phone": "+46 31 555 0456", "website": "http://fiskmarknad.se", "country": "Sweden", "industry": "Food"},
    {"business_name": "Malmö Bike Tours", "address": "Stortorget 789, 211 22 Malmö, Sweden", "phone": "+46 40 555 0789", "website": None, "country": "Sweden", "industry": "Tourism"},
]

# Pre-generated AI pitches and proposals for different scenarios
def get_pitch_for_business(business: dict) -> dict:
    has_website = business.get("website") is not None
    industry = business.get("industry", "General")
    
    if not has_website:
        # No website pitches
        pitches = [
            f"I noticed {business['business_name']} doesn't have a website yet. In today's digital world, over 80% of customers search online before visiting a business. A professional website could help you reach hundreds of new customers in {business.get('country', 'your area')}.",
            f"Hi! I came across {business['business_name']} and noticed you're missing out on online customers. A modern website for your {industry.lower()} business could increase your visibility and bring in 30-50% more customers.",
            f"{business['business_name']} could benefit greatly from an online presence. Your competitors likely have websites - let's make sure potential customers can find YOU when they search for {industry.lower()} services.",
        ]
        
        proposals = [
            f"• Create a professional, mobile-responsive website for {business['business_name']}\n• Set up Google Business Profile optimization\n• Implement local SEO for {business.get('country', 'your region')}\n• Add online booking/contact forms\n• Social media integration\n• Estimated timeline: 2-3 weeks",
            f"• Design custom website showcasing your {industry.lower()} services\n• Mobile-first responsive design\n• Contact forms and click-to-call functionality\n• Google Maps integration showing your location\n• Basic SEO setup to rank in local searches\n• Optional: Online appointment scheduling",
            f"• Modern website design tailored for {industry}\n• Fast-loading, SEO-optimized pages\n• Customer testimonial section\n• Service/menu pages\n• Integration with social media\n• Analytics dashboard to track visitors",
        ]
        
        issues = [
            "No website - missing 80% of potential online customers",
            "Cannot be found in Google searches",
            "No online presence compared to competitors",
            "Missing opportunities for online bookings/inquiries"
        ]
    else:
        # Has website but needs improvement
        pitches = [
            f"I reviewed {business['business_name']}'s website and found several opportunities for improvement. Modern website standards have changed significantly - an updated design could improve your conversion rate by 40%.",
            f"Your website at {business.get('website')} may be losing potential customers due to outdated design patterns. I'd love to help modernize it and improve your online presence.",
            f"{business['business_name']}'s website could use a refresh! Mobile users make up 60% of web traffic now, and an optimized site could significantly boost your {industry.lower()} business.",
        ]
        
        proposals = [
            f"• Website redesign with modern aesthetics\n• Mobile responsiveness optimization\n• Page speed improvements (affects Google ranking)\n• SEO audit and optimization\n• Updated contact/booking system\n• Security updates (SSL, etc.)",
            f"• Full website audit and UX improvement\n• Modern, clean design refresh\n• Mobile optimization for all devices\n• Improved call-to-action buttons\n• Integration with current marketing tools\n• Performance optimization",
            f"• Redesign with conversion-focused layout\n• Speed optimization (current sites often load slowly)\n• Add customer reviews section\n• Update service pages with better content\n• Implement live chat or contact widgets\n• Analytics setup for tracking ROI",
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

# Google Maps API helper
async def search_businesses_google(query: str, location: str = None) -> List[dict]:
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return []
    
    search_query = query
    if location:
        search_query = f"{query} in {location}"
    
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": search_query,
        "key": api_key
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(url, params=params)
            data = response.json()
            
            results = []
            for place in data.get("results", [])[:10]:
                place_id = place.get("place_id")
                
                details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                details_params = {
                    "place_id": place_id,
                    "fields": "name,formatted_address,formatted_phone_number,website,geometry",
                    "key": api_key
                }
                
                details_response = await http_client.get(details_url, params=details_params)
                details = details_response.json().get("result", {})
                
                results.append({
                    "business_name": details.get("name", place.get("name", "Unknown")),
                    "address": details.get("formatted_address", place.get("formatted_address", "")),
                    "phone": details.get("formatted_phone_number"),
                    "website": details.get("website"),
                    "has_website": bool(details.get("website")),
                    "location": {
                        "lat": place.get("geometry", {}).get("location", {}).get("lat", 0),
                        "lng": place.get("geometry", {}).get("location", {}).get("lng", 0)
                    },
                    "industry": "Local Business",
                    "country": "Various"
                })
            
            return results
    except Exception as e:
        logging.error(f"Google Maps API error: {str(e)}")
        return []

# Generate fake lead for padding
def generate_fake_lead() -> dict:
    fake_names = [
        "Sunrise Bakery", "Mountain View Auto", "Coastal Cleaning Co", 
        "Urban Fitness Studio", "Green Thumb Gardens", "Swift Delivery Services",
        "Harmony Music School", "Elite Pet Care", "Precision Plumbing",
        "Bright Ideas Marketing"
    ]
    fake_cities = [
        "New York, NY, USA", "Los Angeles, CA, USA", "Chicago, IL, USA", 
        "London, UK", "Toronto, Canada", "Sydney, Australia",
        "Berlin, Germany", "Paris, France", "Tokyo, Japan", "Dubai, UAE"
    ]
    
    business_name = random.choice(fake_names) + " " + ''.join(random.choices(string.digits, k=3))
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', business_name.lower())[:15]
    
    return {
        "id": str(uuid.uuid4()),
        "business_name": business_name,
        "address": f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Park Blvd', 'Commerce Dr'])}, {random.choice(fake_cities)}",
        "phone": f"+1 ({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
        "email": f"info@{clean_name}.com",
        "website": None,
        "has_website": False,
        "website_issues": ["No website exists - prime opportunity!"],
        "ai_pitch": "This business has no online presence! Help them establish a professional website to reach more customers and grow their business.",
        "ai_proposal": "• Create a modern, mobile-responsive website\n• Set up Google Business Profile\n• Implement basic SEO\n• Add contact forms and booking system\n• Social media integration",
        "location": {"lat": 0, "lng": 0},
        "is_fake": True
    }

# Auth Routes
@api_router.post("/auth/register")
async def register(user_data: UserRegister, response: Response):
    email = user_data.email.lower()
    
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "email": email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "role": "user",
        "subscription_status": "pending",
        "leads_remaining": 0,
        "total_leads_received": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id,
        "email": email,
        "name": user_data.name,
        "role": "user",
        "subscription_status": "pending",
        "leads_remaining": 0,
        "total_leads_received": 0
    }

@api_router.post("/auth/login")
async def login(user_data: UserLogin, response: Response):
    email = user_data.email.lower()
    
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id,
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "subscription_status": user.get("subscription_status", "pending"),
        "leads_remaining": user.get("leads_remaining", 0),
        "total_leads_received": user.get("total_leads_received", 0)
    }

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return {
        "id": user["_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "subscription_status": user.get("subscription_status", "pending"),
        "leads_remaining": user.get("leads_remaining", 0),
        "total_leads_received": user.get("total_leads_received", 0)
    }

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out successfully"}

# Payment Routes
@api_router.post("/payments/process")
async def process_payment(payment: PaymentCreate, request: Request):
    user = await get_current_user(request)
    user_id = str(user["_id"]) if isinstance(user["_id"], ObjectId) else user["_id"]
    
    signup_leads = int(os.environ.get("SIGNUP_LEADS", 250))
    monthly_leads = int(os.environ.get("MONTHLY_LEADS", 100))
    tester_leads = int(os.environ.get("TESTER_LEADS", 50))
    
    # Determine leads based on payment type
    if payment.payment_type == "tester":
        leads_to_add = tester_leads
        new_status = "tester"
    elif payment.payment_type == "signup":
        leads_to_add = signup_leads
        new_status = "active"
    else:  # monthly/refill
        leads_to_add = monthly_leads
        new_status = "active"
    
    # Record payment
    payment_doc = {
        "user_id": user_id,
        "payment_type": payment.payment_type,
        "paypal_order_id": payment.paypal_order_id,
        "amount": payment.amount,
        "leads_granted": leads_to_add,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payments.insert_one(payment_doc)
    
    
    new_status = "active"
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {"subscription_status": new_status},
            "$inc": {
                "leads_remaining": leads_to_add,
                "total_leads_received": leads_to_add
            }
        }
    )
    
    # AUTO-GENERATE LEADS IMMEDIATELY AFTER PAYMENT
    generated_leads = []
    
    # Get unassigned leads from pool
    unassigned_leads = await db.lead_pool.find(
        {"is_assigned": False}
    ).limit(leads_to_add + 20).to_list(leads_to_add + 20)
    
    random.shuffle(unassigned_leads)
    
    for lead_doc in unassigned_leads:
        if len(generated_leads) >= leads_to_add:
            break
        
        # Check if already assigned to this user
        existing = await db.assigned_leads.find_one({
            "user_id": user_id,
            "business_name": lead_doc["business_name"],
            "address": lead_doc["address"]
        })
        
        if existing:
            continue
        
        # Mark as assigned in pool
        await db.lead_pool.update_one(
            {"_id": lead_doc["_id"]},
            {"$set": {"is_assigned": True, "assigned_to": user_id}}
        )
        
        # Try to extract email from website
        email = lead_doc.get("email")
        if not email and lead_doc.get("website"):
            try:
                email = await extract_email_from_website(lead_doc.get("website"))
            except:
                pass
        if not email:
            email = generate_likely_email(lead_doc["business_name"], lead_doc.get("website"))
        
        # Create assigned lead
        assigned_lead = {
            "id": lead_doc.get("id", str(uuid.uuid4())),
            "user_id": user_id,
            "business_name": lead_doc["business_name"],
            "address": lead_doc["address"],
            "phone": lead_doc.get("phone"),
            "email": email,
            "website": lead_doc.get("website"),
            "has_website": lead_doc.get("has_website", False),
            "website_issues": lead_doc.get("website_issues", ["No website"]),
            "ai_pitch": lead_doc.get("ai_pitch", "This business needs a website!"),
            "ai_proposal": lead_doc.get("ai_proposal", "• Create a professional website"),
            "location": lead_doc.get("location", {"lat": 0, "lng": 0}),
            "country": lead_doc.get("country", "Unknown"),
            "industry": lead_doc.get("industry", "General"),
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "is_fake": lead_doc.get("is_fake", False)
        }
        
        await db.assigned_leads.insert_one(assigned_lead)
        generated_leads.append(assigned_lead)
    
    # Add fake leads (1 per 10 real)
    fake_count = max(1, len(generated_leads) // 10)
    for _ in range(fake_count):
        fake_lead = generate_fake_lead()
        fake_lead["user_id"] = user_id
        fake_lead["assigned_at"] = datetime.now(timezone.utc).isoformat()
        await db.assigned_leads.insert_one(fake_lead)
        generated_leads.append(fake_lead)
    
    # Deduct generated leads from remaining
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"leads_remaining": -len(generated_leads)}}
    )
    
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    return {
        "success": True,
        "leads_granted": leads_to_add,
        "leads_generated": len(generated_leads),
        "leads_remaining": updated_user.get("leads_remaining", 0),
        "subscription_status": new_status
    }

@api_router.get("/payments/history")
async def get_payment_history(request: Request):
    user = await get_current_user(request)
    payments = await db.payments.find(
        {"user_id": user["_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return payments

# Lead Routes
@api_router.post("/leads/generate")
async def generate_leads(request: Request):
    user = await get_current_user(request)
    user_id = str(user["_id"]) if isinstance(user["_id"], ObjectId) else user["_id"]
    leads_remaining = user.get("leads_remaining", 0)
    
    if leads_remaining <= 0:
        raise HTTPException(status_code=400, detail="No leads remaining. Please purchase more leads.")
    
    all_leads = []
    leads_to_generate = min(leads_remaining, 50)
    
    # First, try to get leads from the lead pool (pre-seeded real businesses)
    unassigned_leads = await db.lead_pool.find(
        {"is_assigned": False}
    ).limit(leads_to_generate + 10).to_list(leads_to_generate + 10)
    
    random.shuffle(unassigned_leads)
    
    for lead_doc in unassigned_leads[:leads_to_generate]:
        if len(all_leads) >= leads_to_generate:
            break
        
        # Check if already assigned to this user
        existing = await db.assigned_leads.find_one({
            "user_id": user_id,
            "business_name": lead_doc["business_name"],
            "address": lead_doc["address"]
        })
        
        if existing:
            continue
        
        # Mark as assigned in pool
        await db.lead_pool.update_one(
            {"_id": lead_doc["_id"]},
            {"$set": {"is_assigned": True, "assigned_to": user_id}}
        )
        
        # Try to extract email from website
        email = lead_doc.get("email")
        if not email and lead_doc.get("website"):
            email = await extract_email_from_website(lead_doc.get("website"))
        if not email:
            email = generate_likely_email(lead_doc["business_name"], lead_doc.get("website"))
        
        # Create assigned lead
        assigned_lead = {
            "id": lead_doc.get("id", str(uuid.uuid4())),
            "user_id": user_id,
            "business_name": lead_doc["business_name"],
            "address": lead_doc["address"],
            "phone": lead_doc.get("phone"),
            "email": email,
            "website": lead_doc.get("website"),
            "has_website": lead_doc.get("has_website", False),
            "website_issues": lead_doc.get("website_issues", ["No website"]),
            "ai_pitch": lead_doc.get("ai_pitch", "This business needs a website!"),
            "ai_proposal": lead_doc.get("ai_proposal", "• Create a professional website"),
            "location": lead_doc.get("location", {"lat": 0, "lng": 0}),
            "country": lead_doc.get("country", "Unknown"),
            "industry": lead_doc.get("industry", "General"),
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "is_fake": lead_doc.get("is_fake", False)
        }
        
        await db.assigned_leads.insert_one(assigned_lead)
        all_leads.append(assigned_lead)
    
    # If not enough from pool, use the hardcoded database
    if len(all_leads) < leads_to_generate:
        available_businesses = random.sample(
            GLOBAL_BUSINESS_DATABASE, 
            min(len(GLOBAL_BUSINESS_DATABASE), leads_to_generate - len(all_leads) + 10)
        )
        
        for business in available_businesses:
            if len(all_leads) >= leads_to_generate:
                break
            
            existing = await db.assigned_leads.find_one({
                "user_id": user_id,
                "business_name": business["business_name"],
                "address": business["address"]
            })
            
            if existing:
                continue
            
            pitch_data = get_pitch_for_business(business)
            
            # Generate email
            email = generate_likely_email(business["business_name"], business.get("website"))
            
            lead = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "business_name": business["business_name"],
                "address": business["address"],
                "phone": business.get("phone"),
                "email": email,
                "website": business.get("website"),
                "has_website": business.get("website") is not None,
                "website_issues": pitch_data["website_issues"],
                "ai_pitch": pitch_data["ai_pitch"],
                "ai_proposal": pitch_data["ai_proposal"],
                "location": {"lat": 0, "lng": 0},
                "country": business.get("country", "Unknown"),
                "industry": business.get("industry", "General"),
                "assigned_at": datetime.now(timezone.utc).isoformat(),
                "is_fake": False
            }
            
            await db.assigned_leads.insert_one(lead)
            all_leads.append(lead)
    
    # Add fake leads (1 per 10 real leads)
    fake_count = max(1, len(all_leads) // 10)
    for _ in range(fake_count):
        fake_lead = generate_fake_lead()
        fake_lead["user_id"] = user_id
        fake_lead["assigned_at"] = datetime.now(timezone.utc).isoformat()
        await db.assigned_leads.insert_one(fake_lead)
        all_leads.append(fake_lead)
    
    # Update user's remaining leads
    if all_leads:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"leads_remaining": -len(all_leads)}}
        )
    
    # Remove MongoDB _id from leads before returning
    clean_leads = []
    for lead in all_leads:
        clean_lead = {k: v for k, v in lead.items() if k != "_id"}
        clean_lead["user_id"] = str(clean_lead.get("user_id", "")) if clean_lead.get("user_id") else None
        clean_leads.append(clean_lead)
    
    return {
        "leads_generated": len(clean_leads),
        "leads": clean_leads
    }

@api_router.get("/leads")
async def get_my_leads(request: Request, skip: int = 0, limit: int = 50):
    user = await get_current_user(request)
    user_id = str(user["_id"])
    
    # Query by string user_id
    leads = await db.assigned_leads.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("assigned_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Clean leads - remove user_id from response
    clean_leads = []
    for lead in leads:
        clean_lead = {k: v for k, v in lead.items() if k != "user_id"}
        clean_leads.append(clean_lead)
    
    total = await db.assigned_leads.count_documents({"user_id": user_id})
    
    return {
        "leads": clean_leads,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.post("/leads/search")
async def search_business(search: BusinessSearchRequest, request: Request):
    user = await get_current_user(request)
    
    if user.get("subscription_status") not in ["active", "lifetime"]:
        raise HTTPException(status_code=403, detail="Active subscription required")
    
    businesses = await search_businesses_google(search.query, search.location)
    
    results = []
    for business in businesses[:10]:
        pitch_data = get_pitch_for_business(business)
        results.append({
            "business_name": business["business_name"],
            "address": business["address"],
            "phone": business.get("phone"),
            "website": business.get("website"),
            "has_website": business.get("has_website", False),
            "website_issues": pitch_data["website_issues"],
            "ai_pitch": pitch_data["ai_pitch"],
            "ai_proposal": pitch_data["ai_proposal"],
            "location": business.get("location", {})
        })
    
    return {"results": results}

# Stats Routes
@api_router.get("/stats")
async def get_stats(request: Request):
    user = await get_current_user(request)
    user_id = str(user["_id"])
    
    total_leads = await db.assigned_leads.count_documents({"user_id": user_id})
    leads_with_website = await db.assigned_leads.count_documents({
        "user_id": user_id,
        "has_website": True
    })
    leads_without_website = await db.assigned_leads.count_documents({
        "user_id": user_id,
        "has_website": False
    })
    
    return {
        "total_leads": total_leads,
        "leads_with_website": leads_with_website,
        "leads_without_website": leads_without_website,
        "leads_remaining": user.get("leads_remaining", 0),
        "subscription_status": user.get("subscription_status", "pending")
    }

# Health check
@api_router.get("/")
async def root():
    return {"message": "Lead Generation API is running"}

# Include the router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://business-leeds-generator-1.onrender.com", "https://business-leeds-generator.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifetime access emails
LIFETIME_ACCESS_EMAILS = [
    "dgawaine@yahoo.com"
]

# Startup event
@app.on_event("startup")
async def startup_event():
    await db.users.create_index("email", unique=True)
    await db.assigned_leads.create_index([("user_id", 1), ("business_name", 1), ("address", 1)])
    await db.payments.create_index("user_id")
    
    # Seed lifetime access users
    for email in LIFETIME_ACCESS_EMAILS:
        existing = await db.users.find_one({"email": email.lower()})
        if existing:
            await db.users.update_one(
                {"email": email.lower()},
                {"$set": {
                    "subscription_status": "lifetime",
                    "leads_remaining": 999999,
                    "is_lifetime": True
                }}
            )
            logger.info(f"Updated lifetime access for: {email}")
    
    logger.info("Database indexes created")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


