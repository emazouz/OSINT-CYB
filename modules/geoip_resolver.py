"""
GeoIP Resolver Module
Resolves IP addresses to geographic locations using free APIs.
"""

import logging
import socket
import requests

logger = logging.getLogger(__name__)


def resolve_ip(hostname):
    """Resolve a hostname to its IP address."""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


def geoip_lookup(ip_or_host, progress_callback=None):
    """
    Look up geographic location for an IP address or hostname.
    Uses ip-api.com (free, no key required, 45 req/min).
    
    Args:
        ip_or_host: IP address or hostname to look up
        progress_callback: Progress callback function
    
    Returns:
        Dict with geolocation data
    """
    if progress_callback:
        progress_callback(f"🌍 تحديد موقع {ip_or_host}...")

    # Resolve hostname to IP if needed
    ip = ip_or_host
    hostname = ip_or_host
    try:
        socket.inet_aton(ip_or_host)
    except socket.error:
        ip = resolve_ip(ip_or_host)
        if not ip:
            return {"error": f"Cannot resolve hostname: {ip_or_host}", "query": ip_or_host}

    result = {
        "query": ip_or_host,
        "ip": ip,
        "hostname": hostname,
        "country": None,
        "country_code": None,
        "region": None,
        "city": None,
        "zip": None,
        "lat": None,
        "lon": None,
        "timezone": None,
        "isp": None,
        "org": None,
        "as_number": None,
        "as_name": None,
        "is_proxy": None,
        "is_hosting": None,
        "error": None,
    }

    try:
        # Primary API: ip-api.com
        resp = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
            f"region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,"
            f"proxy,hosting,query",
            timeout=10
        )
        data = resp.json()

        if data.get("status") == "success":
            result.update({
                "country": data.get("country"),
                "country_code": data.get("countryCode"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "zip": data.get("zip"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "timezone": data.get("timezone"),
                "isp": data.get("isp"),
                "org": data.get("org"),
                "as_number": data.get("as"),
                "as_name": data.get("asname"),
                "is_proxy": data.get("proxy"),
                "is_hosting": data.get("hosting"),
            })

            if progress_callback:
                progress_callback(
                    f"✅ الموقع: {result['city']}, {result['country']} ({result['isp']})"
                )
        else:
            result["error"] = data.get("message", "Unknown error")

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"GeoIP lookup failed for {ip}: {e}")

    return result


def bulk_geoip(targets, progress_callback=None):
    """Look up multiple IPs/hostnames."""
    results = []
    for i, target in enumerate(targets):
        if progress_callback:
            progress_callback(f"🌍 GeoIP {i+1}/{len(targets)}: {target}")
        results.append(geoip_lookup(target))
    return results
