"""
WHOIS Lookup Module
Extracts domain registration information: registrar, dates, nameservers, registrant.
"""

import logging
import whois
from datetime import datetime

logger = logging.getLogger(__name__)


def whois_lookup(domain):
    """Perform WHOIS lookup on a domain and return structured results."""
    result = {
        "domain": domain,
        "registrar": None,
        "creation_date": None,
        "expiration_date": None,
        "updated_date": None,
        "nameservers": [],
        "status": [],
        "registrant": None,
        "registrant_country": None,
        "emails": [],
        "dnssec": None,
        "org": None,
        "address": None,
        "city": None,
        "state": None,
        "zipcode": None,
        "country": None,
        "raw": None,
        "error": None,
    }

    try:
        w = whois.whois(domain)

        result["registrar"] = w.registrar
        result["org"] = w.org

        # Handle dates (can be list or single value)
        if w.creation_date:
            cd = w.creation_date if not isinstance(w.creation_date, list) else w.creation_date[0]
            result["creation_date"] = cd.isoformat() if isinstance(cd, datetime) else str(cd)

        if w.expiration_date:
            ed = w.expiration_date if not isinstance(w.expiration_date, list) else w.expiration_date[0]
            result["expiration_date"] = ed.isoformat() if isinstance(ed, datetime) else str(ed)

        if w.updated_date:
            ud = w.updated_date if not isinstance(w.updated_date, list) else w.updated_date[0]
            result["updated_date"] = ud.isoformat() if isinstance(ud, datetime) else str(ud)

        # Nameservers
        if w.name_servers:
            ns = w.name_servers if isinstance(w.name_servers, list) else [w.name_servers]
            result["nameservers"] = [str(n).lower() for n in ns]

        # Status
        if w.status:
            status = w.status if isinstance(w.status, list) else [w.status]
            result["status"] = [str(s) for s in status]

        # Emails
        if w.emails:
            emails = w.emails if isinstance(w.emails, list) else [w.emails]
            result["emails"] = emails

        # Location info
        result["address"] = w.address
        result["city"] = w.city
        result["state"] = w.state
        result["zipcode"] = w.zipcode
        result["country"] = w.country
        result["dnssec"] = str(w.dnssec) if w.dnssec else None

        # Calculate domain age
        if result["creation_date"]:
            try:
                created = datetime.fromisoformat(result["creation_date"])
                age_days = (datetime.now() - created).days
                result["domain_age_days"] = age_days
                result["domain_age_years"] = round(age_days / 365.25, 1)
            except Exception:
                pass

        logger.info(f"WHOIS lookup successful for {domain}")

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"WHOIS lookup failed for {domain}: {e}")

    return result


def bulk_whois(domains, progress_callback=None):
    """Perform WHOIS lookups on multiple domains."""
    results = []
    for i, domain in enumerate(domains):
        if progress_callback:
            progress_callback(f"WHOIS {i+1}/{len(domains)}: {domain}")
        results.append(whois_lookup(domain))
    return results
