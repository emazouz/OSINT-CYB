"""
Email Harvesting Module
Extracts email addresses from search results, page content, and known patterns.
"""

import re
import logging
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Comprehensive email regex
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

# Common email patterns for organizations
COMMON_PATTERNS = [
    "{first}.{last}@{domain}",
    "{first}{last}@{domain}",
    "{f}{last}@{domain}",
    "{first}@{domain}",
    "{last}@{domain}",
    "info@{domain}",
    "contact@{domain}",
    "admin@{domain}",
    "support@{domain}",
    "hello@{domain}",
    "sales@{domain}",
    "hr@{domain}",
    "careers@{domain}",
    "press@{domain}",
    "media@{domain}",
    "webmaster@{domain}",
    "postmaster@{domain}",
    "abuse@{domain}",
    "security@{domain}",
    "privacy@{domain}",
]

# Blacklisted email domains (false positives)
BLACKLIST_DOMAINS = {
    "example.com", "test.com", "localhost", "email.com",
    "domain.com", "yoursite.com", "yourdomain.com",
    "sentry.io", "wixpress.com", "w3.org",
}


def extract_emails_from_text(text):
    """Extract email addresses from raw text."""
    if not text:
        return []

    emails = EMAIL_REGEX.findall(text)

    # Filter out false positives
    valid_emails = []
    for email in emails:
        email = email.lower().strip()
        domain = email.split("@")[1] if "@" in email else ""

        # Skip blacklisted domains
        if domain in BLACKLIST_DOMAINS:
            continue

        # Skip image/file extensions misidentified as emails
        if any(email.endswith(ext) for ext in [".png", ".jpg", ".gif", ".svg", ".css", ".js"]):
            continue

        if email not in valid_emails:
            valid_emails.append(email)

    return valid_emails


def extract_emails_from_url(url, timeout=10):
    """Fetch a URL and extract email addresses from its content."""
    emails = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, timeout=timeout, headers=headers, verify=False)
        if resp.status_code == 200:
            emails = extract_emails_from_text(resp.text)
    except Exception as e:
        logger.debug(f"Failed to fetch {url} for email extraction: {e}")
    return emails


def harvest_emails(search_results, query="", max_pages=10, progress_callback=None):
    """
    Harvest emails from search results and their linked pages.
    
    Args:
        search_results: List of search result dicts with 'link', 'title', 'snippet'
        query: Original search query
        max_pages: Maximum number of pages to scrape for emails
        progress_callback: Function to report progress
    
    Returns:
        Dict with found emails and their sources
    """
    all_emails = {}

    # Extract from snippets first (fast)
    if progress_callback:
        progress_callback("📧 استخراج الإيميلات من النتائج...")

    for result in search_results:
        snippet = result.get("snippet", "")
        title = result.get("title", "")
        link = result.get("link", "")

        found = extract_emails_from_text(f"{snippet} {title} {link}")
        for email in found:
            if email not in all_emails:
                all_emails[email] = {
                    "email": email,
                    "sources": [],
                    "domain": email.split("@")[1],
                }
            all_emails[email]["sources"].append({
                "url": link,
                "title": title,
                "method": "snippet_extraction"
            })

    # Deep extraction: visit linked pages
    if progress_callback:
        progress_callback("📧 فحص الصفحات المرتبطة...")

    pages_scanned = 0
    for result in search_results:
        if pages_scanned >= max_pages:
            break

        link = result.get("link", "")
        if not link or not link.startswith("http"):
            continue

        # Skip social media and known non-useful pages
        skip_domains = ["facebook.com", "twitter.com", "instagram.com", "youtube.com", "tiktok.com"]
        if any(d in link.lower() for d in skip_domains):
            continue

        if progress_callback:
            progress_callback(f"📧 فحص: {link[:60]}...")

        found = extract_emails_from_url(link)
        for email in found:
            if email not in all_emails:
                all_emails[email] = {
                    "email": email,
                    "sources": [],
                    "domain": email.split("@")[1],
                }
            all_emails[email]["sources"].append({
                "url": link,
                "title": result.get("title", ""),
                "method": "page_scrape"
            })

        pages_scanned += 1

    if progress_callback:
        progress_callback(f"✅ تم العثور على {len(all_emails)} بريد إلكتروني")

    return {
        "emails": list(all_emails.values()),
        "total_found": len(all_emails),
        "pages_scanned": pages_scanned,
        "unique_domains": list(set(e["domain"] for e in all_emails.values())),
    }
