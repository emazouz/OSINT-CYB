# OSINT Analyzer Ultimate — Setup Steps

## 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

## 2. Install Playwright browsers
```bash
playwright install chromium
```

## 3. Run the application
```bash
python app.py
```

## 4. Open the dashboard
Open your browser and navigate to: **http://localhost:5000**

---

## Available API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/search` | POST | Multi-engine search (DuckDuckGo + Dorking) |
| `/api/dns` | POST | DNS enumeration |
| `/api/whois` | POST | WHOIS lookup |
| `/api/ssl` | POST | SSL/TLS inspection |
| `/api/ports` | POST | Port scanning |
| `/api/subdomains` | POST | Subdomain discovery |
| `/api/tech` | POST | Technology detection |
| `/api/headers` | POST | HTTP header analysis |
| `/api/geoip` | POST | GeoIP location lookup |
| `/api/username` | POST | Username checker (30+ platforms) |
| `/api/wayback` | POST | Wayback Machine lookup |
| `/api/emails` | POST | Email extraction |
| `/api/phones` | POST | Phone number extraction |
| `/api/social` | POST | Social media profile extraction |
| `/api/full-scan` | POST | Complete domain scan (all tools) |