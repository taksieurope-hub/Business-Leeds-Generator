# ProspectRadar - MVP PRD

## Original Problem Statement
Build a lean MVP lead generation platform that finds 10 high-quality leads per day and helps close 1 deal. The app searches the internet for businesses with outdated/no websites, scans social media for "need a website" posts, and finds free/expiring domains.

## User Personas
1. **Freelance Web Developer** - Looking for leads to sell website services ($299-$999)
2. **Digital Agency** - Finding businesses that need website upgrades
3. **Lead Reseller** - Aggregating and selling hot leads to other freelancers

## Core Requirements (Static)
- Lead discovery from multiple sources (Google Maps, Reddit, Facebook, job boards)
- Lead scoring system (Hot/Warm/Cold based on website quality, reviews, activity)
- Contact extraction (email, phone, social links)
- Website audit reports (SEO, speed, mobile, missing features)
- AI-powered sales pitch and proposal generation
- CRM pipeline (New/Contacted/Replied/Closed/Lost)
- Email and WhatsApp outreach automation
- Domain finder with AI suggestions
- Manual mode (edit leads, approve before outreach)
- Country filters (South Africa, UK, USA)

## What's Been Implemented (March 28, 2026)

### Backend (FastAPI + MongoDB)
- ✅ Lead CRUD operations (create, read, update, delete)
- ✅ Lead scanning with mock data (simulates Google Maps/Reddit/Facebook)
- ✅ Lead scoring algorithm (calculates Hot/Warm/Cold based on multiple factors)
- ✅ Revenue opportunity calculator
- ✅ Website audit scores (mock SEO/Speed/Mobile analysis)
- ✅ AI pitch generation (OpenAI GPT-5.2 via Emergent LLM)
- ✅ AI proposal generation with pricing tiers
- ✅ Email outreach endpoint (mocked - Resend not configured)
- ✅ WhatsApp outreach endpoint (mocked - Twilio credentials need Account SID format)
- ✅ Domain suggestions API
- ✅ Dashboard stats endpoint

### Frontend (React + Shadcn UI)
- ✅ Dashboard with stats cards (Total Leads, Hot Leads, Closed Deals, Revenue)
- ✅ Lead list with Hot/Warm/Cold badges and status badges
- ✅ Filters (status, score, country) and search
- ✅ Add Lead modal for manual entry
- ✅ Lead detail page with Website Audit display
- ✅ AI Pitch and Proposal tabs with generation buttons
- ✅ Domain suggestions with match scores
- ✅ Send Email and Send WhatsApp modals
- ✅ Status change dropdown
- ✅ Edit and Delete lead functionality
- ✅ Domain Finder page
- ✅ Settings page with integration status

## Prioritized Backlog

### P0 - Critical (Next Sprint)
- [ ] Configure real Resend API key for email outreach
- [ ] Get Twilio Account SID (not API Key) for WhatsApp

### P1 - High Priority
- [ ] Real web scraping for Google Maps/Yelp businesses
- [ ] Reddit/Facebook "need website" post monitoring
- [ ] Demo website screenshot generator
- [ ] Email sequence automation (Day 1, 3, 7 follow-ups)

### P2 - Medium Priority
- [ ] Chrome extension for manual lead capture
- [ ] Competitor comparison feature
- [ ] "Before vs After" visual mockups
- [ ] Bulk outreach actions
- [ ] Export leads to CSV

### P3 - Nice to Have
- [ ] Mobile app alerts for hot leads
- [ ] Lead marketplace (sell leads to others)
- [ ] Multi-user/team support
- [ ] Payment integration for subscriptions

## Next Tasks
1. Get Resend API key and configure email outreach
2. Get Twilio Account SID (starts with 'AC') for WhatsApp
3. Add email sequence automation
4. Implement real scraping for at least one source
