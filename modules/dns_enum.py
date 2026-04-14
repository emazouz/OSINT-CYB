"""
DNS Enumeration Module
Performs comprehensive DNS record lookups: A, AAAA, MX, NS, TXT, CNAME, SOA, SRV, PTR.
"""

import logging
import dns.resolver
import dns.reversename
import socket

logger = logging.getLogger(__name__)

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "SRV", "CAA"]


def dns_enumerate(domain, progress_callback=None):
    """Perform full DNS enumeration on a domain."""
    result = {
        "domain": domain,
        "records": {},
        "all_ips": [],
        "mail_servers": [],
        "nameservers": [],
        "txt_records": [],
        "has_spf": False,
        "has_dmarc": False,
        "has_dkim": False,
        "error": None,
    }

    resolver = dns.resolver.Resolver()
    resolver.timeout = 10
    resolver.lifetime = 10

    for rtype in RECORD_TYPES:
        if progress_callback:
            progress_callback(f"DNS {rtype} → {domain}")
        try:
            answers = resolver.resolve(domain, rtype)
            records = []
            for rdata in answers:
                record_str = rdata.to_text()
                records.append(record_str)

                # Collect IPs
                if rtype in ("A", "AAAA"):
                    result["all_ips"].append(record_str)

                # Collect mail servers
                if rtype == "MX":
                    result["mail_servers"].append({
                        "priority": rdata.preference,
                        "server": str(rdata.exchange).rstrip(".")
                    })

                # Collect nameservers
                if rtype == "NS":
                    result["nameservers"].append(record_str.rstrip("."))

                # Analyze TXT records
                if rtype == "TXT":
                    result["txt_records"].append(record_str)
                    txt_lower = record_str.lower()
                    if "v=spf1" in txt_lower:
                        result["has_spf"] = True
                    if "v=dmarc1" in txt_lower:
                        result["has_dmarc"] = True
                    if "v=dkim1" in txt_lower:
                        result["has_dkim"] = True

            result["records"][rtype] = records
        except dns.resolver.NoAnswer:
            result["records"][rtype] = []
        except dns.resolver.NXDOMAIN:
            result["error"] = f"Domain {domain} does not exist"
            break
        except dns.resolver.NoNameservers:
            result["records"][rtype] = []
        except Exception as e:
            result["records"][rtype] = []
            logger.debug(f"DNS {rtype} for {domain}: {e}")

    # Check DMARC specifically
    try:
        dmarc_answers = resolver.resolve(f"_dmarc.{domain}", "TXT")
        for rdata in dmarc_answers:
            txt = rdata.to_text().lower()
            if "v=dmarc1" in txt:
                result["has_dmarc"] = True
                result["records"]["DMARC"] = [rdata.to_text()]
    except Exception:
        pass

    # Reverse DNS for found IPs
    result["reverse_dns"] = {}
    for ip in result["all_ips"][:5]:
        try:
            rev_name = dns.reversename.from_address(ip)
            rev_answers = resolver.resolve(rev_name, "PTR")
            result["reverse_dns"][ip] = [str(r).rstrip(".") for r in rev_answers]
        except Exception:
            result["reverse_dns"][ip] = []

    # Email security score
    score = 0
    if result["has_spf"]:
        score += 33
    if result["has_dmarc"]:
        score += 34
    if result["has_dkim"]:
        score += 33
    result["email_security_score"] = score

    logger.info(f"DNS enumeration complete for {domain}: {len(result['all_ips'])} IPs found")
    return result
