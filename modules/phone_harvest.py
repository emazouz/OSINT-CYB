"""
Phone Number Harvesting Module
Extracts and validates phone numbers from text and web pages.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Phone number patterns for various countries
PHONE_PATTERNS = [
    # International format
    re.compile(r'\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{2,4}[\s\-]?\d{2,4}[\s\-]?\d{0,4}'),
    # US/Canada: (xxx) xxx-xxxx or xxx-xxx-xxxx
    re.compile(r'\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}'),
    # International with spaces
    re.compile(r'\+\d{1,3}\s\d{2,4}\s\d{2,4}\s\d{2,4}'),
    # Morocco format
    re.compile(r'(?:\+212|0)[\s\-]?[5-7]\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}'),
    # UK format
    re.compile(r'(?:\+44|0)\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}'),
    # Generic international
    re.compile(r'\+\d{10,15}'),
]

# Keywords that often appear near phone numbers
PHONE_CONTEXT_KEYWORDS = [
    "phone", "tel", "telephone", "mobile", "cell", "call", "fax",
    "contact", "whatsapp", "viber", "signal",
    "هاتف", "جوال", "موبايل", "اتصل", "رقم",
    "téléphone", "numéro", "appeler",
]


def extract_phones_from_text(text):
    """Extract phone numbers from raw text."""
    if not text:
        return []

    phones = set()
    for pattern in PHONE_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            # Clean up the number
            cleaned = re.sub(r'[\s\(\)\-\.]', '', match)
            if len(cleaned) >= 8 and len(cleaned) <= 16:
                phones.add(match.strip())

    return list(phones)


def harvest_phones(search_results, progress_callback=None):
    """
    Harvest phone numbers from search results.
    
    Args:
        search_results: List of search result dicts
        progress_callback: Function to report progress
    
    Returns:
        Dict with found phone numbers and their sources
    """
    all_phones = {}

    if progress_callback:
        progress_callback("📞 استخراج أرقام الهواتف...")

    for result in search_results:
        snippet = result.get("snippet", "")
        title = result.get("title", "")
        link = result.get("link", "")

        # Combine all text for extraction
        text = f"{snippet} {title} {link}"
        found = extract_phones_from_text(text)

        for phone in found:
            cleaned = re.sub(r'[\s\(\)\-\.]', '', phone)
            if cleaned not in all_phones:
                all_phones[cleaned] = {
                    "number": phone,
                    "cleaned": cleaned,
                    "sources": [],
                    "country": detect_country(cleaned),
                }
            all_phones[cleaned]["sources"].append({
                "url": link,
                "title": title,
            })

    if progress_callback:
        progress_callback(f"✅ تم العثور على {len(all_phones)} رقم هاتف")

    return {
        "phones": list(all_phones.values()),
        "total_found": len(all_phones),
    }


def detect_country(phone_number):
    """Detect country from phone number prefix."""
    prefixes = {
        "+1": "US/Canada",
        "+44": "UK",
        "+33": "France",
        "+212": "Morocco",
        "+49": "Germany",
        "+39": "Italy",
        "+34": "Spain",
        "+81": "Japan",
        "+86": "China",
        "+91": "India",
        "+61": "Australia",
        "+55": "Brazil",
        "+7": "Russia",
        "+90": "Turkey",
        "+966": "Saudi Arabia",
        "+971": "UAE",
        "+20": "Egypt",
        "+213": "Algeria",
        "+216": "Tunisia",
        "+218": "Libya",
        "+249": "Sudan",
        "+962": "Jordan",
        "+961": "Lebanon",
        "+963": "Syria",
        "+964": "Iraq",
        "+965": "Kuwait",
        "+968": "Oman",
        "+974": "Qatar",
        "+973": "Bahrain",
    }
    for prefix, country in sorted(prefixes.items(), key=lambda x: -len(x[0])):
        if phone_number.startswith(prefix):
            return country
    return "Unknown"
