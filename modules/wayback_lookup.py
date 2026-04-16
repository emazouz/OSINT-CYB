"""
Wayback Machine Lookup Module
Queries the Internet Archive's Wayback Machine for historical snapshots of a URL.
"""

import logging
import requests

logger = logging.getLogger(__name__)


def wayback_lookup(url, limit=20, progress_callback=None):
    """
    Look up historical snapshots of a URL in the Wayback Machine.
    
    Args:
        url: Target URL or domain
        limit: Maximum number of snapshots to return
        progress_callback: Progress callback function
    
    Returns:
        Dict with snapshot history and availability info
    """
    if progress_callback:
        progress_callback(f"📜 البحث في أرشيف الإنترنت عن {url}...")

    result = {
        "url": url,
        "available": False,
        "first_snapshot": None,
        "latest_snapshot": None,
        "total_snapshots": 0,
        "snapshots": [],
        "years_active": [],
        "error": None,
    }

    # Check availability first
    try:
        avail_resp = requests.get(
            f"https://archive.org/wayback/available?url={url}",
            timeout=15
        )
        avail_data = avail_resp.json()
        
        if avail_data.get("archived_snapshots", {}).get("closest"):
            closest = avail_data["archived_snapshots"]["closest"]
            result["available"] = closest.get("available", False)
            result["latest_snapshot"] = {
                "url": closest.get("url"),
                "timestamp": closest.get("timestamp"),
                "status": closest.get("status"),
            }
    except Exception as e:
        logger.warning(f"Wayback availability check failed: {e}")

    # Get CDX (snapshot index) data
    try:
        cdx_url = (
            f"https://web.archive.org/cdx/search/cdx?"
            f"url={url}&output=json&limit={limit}&fl=timestamp,original,statuscode,digest,length"
            f"&collapse=timestamp:6"  # Collapse by year-month for unique snapshots
        )
        cdx_resp = requests.get(cdx_url, timeout=20)
        
        if cdx_resp.status_code == 200:
            data = cdx_resp.json()
            
            if len(data) > 1:  # First row is headers
                headers = data[0]
                snapshots = []
                years = set()

                for row in data[1:]:
                    snapshot = dict(zip(headers, row))
                    timestamp = snapshot.get("timestamp", "")
                    year = timestamp[:4] if len(timestamp) >= 4 else ""
                    
                    if year:
                        years.add(year)
                    
                    snapshots.append({
                        "timestamp": timestamp,
                        "date": f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}" if len(timestamp) >= 8 else timestamp,
                        "url": f"https://web.archive.org/web/{timestamp}/{snapshot.get('original', url)}",
                        "original_url": snapshot.get("original", url),
                        "status_code": snapshot.get("statuscode"),
                        "content_length": snapshot.get("length"),
                    })

                result["snapshots"] = snapshots
                result["total_snapshots"] = len(snapshots)
                result["years_active"] = sorted(years)
                
                if snapshots:
                    result["first_snapshot"] = snapshots[0]
                    result["latest_snapshot"] = snapshots[-1]
                    result["available"] = True

                if progress_callback:
                    progress_callback(
                        f"✅ وُجد {len(snapshots)} لقطة من {min(years) if years else '?'} "
                        f"إلى {max(years) if years else '?'}"
                    )

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Wayback CDX query failed: {e}")
        if progress_callback:
            progress_callback(f"⚠️ فشل البحث في الأرشيف: {e}")

    return result


def compare_snapshots(url, timestamp1, timestamp2, progress_callback=None):
    """
    Get two snapshots for comparison (returns URLs to view them).
    """
    return {
        "snapshot1": f"https://web.archive.org/web/{timestamp1}/{url}",
        "snapshot2": f"https://web.archive.org/web/{timestamp2}/{url}",
        "diff_url": f"https://web.archive.org/web/diff/{timestamp1}/{timestamp2}/{url}",
    }
