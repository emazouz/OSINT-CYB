"""
Username Checker Module
Checks if a username exists across 30+ platforms.
"""

import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Platform definitions: name -> (url_template, method, indicators)
PLATFORMS = {
    "GitHub": {
        "url": "https://github.com/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-github",
        "color": "#333",
    },
    "Twitter/X": {
        "url": "https://x.com/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-twitter",
        "color": "#1DA1F2",
    },
    "Instagram": {
        "url": "https://www.instagram.com/{username}/",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-instagram",
        "color": "#E1306C",
    },
    "Reddit": {
        "url": "https://www.reddit.com/user/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-reddit",
        "color": "#FF4500",
    },
    "Pinterest": {
        "url": "https://www.pinterest.com/{username}/",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-pinterest",
        "color": "#bd081c",
    },
    "TikTok": {
        "url": "https://www.tiktok.com/@{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-tiktok",
        "color": "#69C9D0",
    },
    "YouTube": {
        "url": "https://www.youtube.com/@{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-youtube",
        "color": "#FF0000",
    },
    "Twitch": {
        "url": "https://www.twitch.tv/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-twitch",
        "color": "#6441a5",
    },
    "Medium": {
        "url": "https://medium.com/@{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-medium",
        "color": "#00ab6c",
    },
    "Dev.to": {
        "url": "https://dev.to/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-dev",
        "color": "#0a0a0a",
    },
    "GitLab": {
        "url": "https://gitlab.com/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-gitlab",
        "color": "#fc6d26",
    },
    "Bitbucket": {
        "url": "https://bitbucket.org/{username}/",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-bitbucket",
        "color": "#0052CC",
    },
    "Keybase": {
        "url": "https://keybase.io/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fas fa-key",
        "color": "#FF6F21",
    },
    "Flickr": {
        "url": "https://www.flickr.com/people/{username}/",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-flickr",
        "color": "#0063dc",
    },
    "VK": {
        "url": "https://vk.com/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-vk",
        "color": "#4a76a8",
    },
    "SoundCloud": {
        "url": "https://soundcloud.com/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-soundcloud",
        "color": "#ff5500",
    },
    "Spotify": {
        "url": "https://open.spotify.com/user/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-spotify",
        "color": "#1DB954",
    },
    "Telegram": {
        "url": "https://t.me/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-telegram",
        "color": "#0088cc",
    },
    "HackerNews": {
        "url": "https://news.ycombinator.com/user?id={username}",
        "method": "content",
        "valid_content": "karma",
        "icon": "fab fa-hacker-news",
        "color": "#ff6600",
    },
    "CodePen": {
        "url": "https://codepen.io/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-codepen",
        "color": "#0ebeff",
    },
    "Dribbble": {
        "url": "https://dribbble.com/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-dribbble",
        "color": "#ea4c89",
    },
    "Behance": {
        "url": "https://www.behance.net/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-behance",
        "color": "#1769ff",
    },
    "Replit": {
        "url": "https://replit.com/@{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fas fa-code",
        "color": "#f26207",
    },
    "Gravatar": {
        "url": "https://en.gravatar.com/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fas fa-user-circle",
        "color": "#1E8CBE",
    },
    "About.me": {
        "url": "https://about.me/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fas fa-user",
        "color": "#00A98F",
    },
    "Patreon": {
        "url": "https://www.patreon.com/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-patreon",
        "color": "#FF424D",
    },
    "npm": {
        "url": "https://www.npmjs.com/~{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-npm",
        "color": "#CB3837",
    },
    "PyPI": {
        "url": "https://pypi.org/user/{username}/",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-python",
        "color": "#3776AB",
    },
    "HackerRank": {
        "url": "https://www.hackerrank.com/{username}",
        "method": "status",
        "valid_status": 200,
        "icon": "fab fa-hackerrank",
        "color": "#2EC866",
    },
    "LeetCode": {
        "url": "https://leetcode.com/{username}/",
        "method": "status",
        "valid_status": 200,
        "icon": "fas fa-code",
        "color": "#FFA116",
    },
}


def check_single_platform(username, platform_name, platform_info, timeout=8):
    """Check if a username exists on a single platform."""
    url = platform_info["url"].format(username=username)
    result = {
        "platform": platform_name,
        "url": url,
        "exists": False,
        "status_code": None,
        "icon": platform_info.get("icon", "fas fa-globe"),
        "color": platform_info.get("color", "#6cf"),
        "error": None,
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        result["status_code"] = resp.status_code

        method = platform_info.get("method", "status")

        if method == "status":
            result["exists"] = resp.status_code == platform_info.get("valid_status", 200)
        elif method == "content":
            valid_content = platform_info.get("valid_content", "")
            result["exists"] = valid_content.lower() in resp.text.lower() and resp.status_code == 200

    except requests.exceptions.Timeout:
        result["error"] = "Timeout"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection Error"
    except Exception as e:
        result["error"] = str(e)

    return result


def check_username(username, max_workers=10, progress_callback=None):
    """
    Check a username across all platforms concurrently.
    
    Args:
        username: The username to check
        max_workers: Number of concurrent threads
        progress_callback: Function to report progress
    
    Returns:
        Dict with found profiles and statistics
    """
    if progress_callback:
        progress_callback(f"👤 فحص المستخدم '{username}' عبر {len(PLATFORMS)} منصة...")

    results = []
    found_count = 0
    total = len(PLATFORMS)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_single_platform, username, name, info): name
            for name, info in PLATFORMS.items()
        }

        for i, future in enumerate(as_completed(futures)):
            platform_name = futures[future]
            try:
                result = future.result()
                results.append(result)
                if result["exists"]:
                    found_count += 1
                if progress_callback and (i + 1) % 5 == 0:
                    progress_callback(f"👤 فحص {i+1}/{total} منصة... ({found_count} وُجد)")
            except Exception as e:
                results.append({
                    "platform": platform_name,
                    "exists": False,
                    "error": str(e),
                })

    # Sort: found first, then alphabetical
    results.sort(key=lambda x: (not x.get("exists", False), x.get("platform", "")))

    if progress_callback:
        progress_callback(f"✅ تم فحص {total} منصة — وُجد {found_count} حساب")

    return {
        "username": username,
        "profiles": results,
        "found_count": found_count,
        "total_checked": total,
        "found_platforms": [r for r in results if r.get("exists")],
        "not_found_platforms": [r for r in results if not r.get("exists")],
    }
