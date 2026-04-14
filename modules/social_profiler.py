"""
Social Media Profiler Module
Builds a social media profile by aggregating data across platforms.
"""

import logging
import requests
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


# Social media site patterns for profile detection
SOCIAL_PLATFORMS = {
    "Facebook": {
        "url_patterns": ["facebook.com/", "fb.com/"],
        "profile_url": "https://www.facebook.com/{username}",
        "api_search": None,
        "icon": "fab fa-facebook",
        "color": "#4267B2",
    },
    "Twitter/X": {
        "url_patterns": ["twitter.com/", "x.com/"],
        "profile_url": "https://x.com/{username}",
        "api_search": None,
        "icon": "fab fa-twitter",
        "color": "#1DA1F2",
    },
    "Instagram": {
        "url_patterns": ["instagram.com/"],
        "profile_url": "https://www.instagram.com/{username}/",
        "api_search": None,
        "icon": "fab fa-instagram",
        "color": "#E1306C",
    },
    "LinkedIn": {
        "url_patterns": ["linkedin.com/in/", "linkedin.com/company/"],
        "profile_url": "https://www.linkedin.com/in/{username}",
        "api_search": None,
        "icon": "fab fa-linkedin",
        "color": "#0077B5",
    },
    "GitHub": {
        "url_patterns": ["github.com/"],
        "profile_url": "https://github.com/{username}",
        "api_url": "https://api.github.com/users/{username}",
        "icon": "fab fa-github",
        "color": "#333",
    },
    "YouTube": {
        "url_patterns": ["youtube.com/", "youtu.be/"],
        "profile_url": "https://www.youtube.com/@{username}",
        "api_search": None,
        "icon": "fab fa-youtube",
        "color": "#FF0000",
    },
    "Reddit": {
        "url_patterns": ["reddit.com/user/", "reddit.com/u/"],
        "profile_url": "https://www.reddit.com/user/{username}",
        "api_url": "https://www.reddit.com/user/{username}/about.json",
        "icon": "fab fa-reddit",
        "color": "#FF4500",
    },
    "TikTok": {
        "url_patterns": ["tiktok.com/@"],
        "profile_url": "https://www.tiktok.com/@{username}",
        "api_search": None,
        "icon": "fab fa-tiktok",
        "color": "#69C9D0",
    },
    "Telegram": {
        "url_patterns": ["t.me/", "telegram.me/"],
        "profile_url": "https://t.me/{username}",
        "api_search": None,
        "icon": "fab fa-telegram",
        "color": "#0088cc",
    },
    "Pinterest": {
        "url_patterns": ["pinterest.com/"],
        "profile_url": "https://www.pinterest.com/{username}/",
        "api_search": None,
        "icon": "fab fa-pinterest",
        "color": "#bd081c",
    },
    "Medium": {
        "url_patterns": ["medium.com/@"],
        "profile_url": "https://medium.com/@{username}",
        "api_search": None,
        "icon": "fab fa-medium",
        "color": "#00ab6c",
    },
    "Twitch": {
        "url_patterns": ["twitch.tv/"],
        "profile_url": "https://www.twitch.tv/{username}",
        "api_search": None,
        "icon": "fab fa-twitch",
        "color": "#6441a5",
    },
}


def extract_profiles_from_results(search_results, progress_callback=None):
    """
    Extract social media profiles from search results.
    
    Args:
        search_results: List of search result dicts
        progress_callback: Progress callback function
    
    Returns:
        Dict with found profiles grouped by platform
    """
    if progress_callback:
        progress_callback("👥 استخراج الملفات الشخصية من النتائج...")

    profiles = {}

    for result in search_results:
        link = result.get("link", "").lower()
        title = result.get("title", "")

        for platform, info in SOCIAL_PLATFORMS.items():
            for pattern in info["url_patterns"]:
                if pattern in link:
                    if platform not in profiles:
                        profiles[platform] = []

                    # Extract username from URL
                    username = _extract_username(link, pattern)

                    profiles[platform].append({
                        "platform": platform,
                        "url": result.get("link", ""),
                        "title": title,
                        "username": username,
                        "snippet": result.get("snippet", ""),
                        "icon": info["icon"],
                        "color": info["color"],
                    })
                    break

    # Enrich GitHub profiles with API data
    if "GitHub" in profiles:
        for profile in profiles["GitHub"]:
            if profile.get("username"):
                api_data = _fetch_github_profile(profile["username"])
                if api_data:
                    profile["api_data"] = api_data

    if progress_callback:
        total = sum(len(p) for p in profiles.values())
        progress_callback(f"✅ وُجد {total} ملف شخصي عبر {len(profiles)} منصة")

    return {
        "profiles": profiles,
        "total_found": sum(len(p) for p in profiles.values()),
        "platforms_found": list(profiles.keys()),
    }


def _extract_username(url, pattern):
    """Extract username from a social media URL."""
    try:
        idx = url.find(pattern)
        if idx >= 0:
            remaining = url[idx + len(pattern):]
            # Take the first path segment
            username = remaining.split("/")[0].split("?")[0].split("#")[0]
            username = username.strip("@")
            return username if username else None
    except Exception:
        pass
    return None


def _fetch_github_profile(username):
    """Fetch public GitHub profile data via API."""
    try:
        resp = requests.get(
            f"https://api.github.com/users/{username}",
            timeout=10,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "name": data.get("name"),
                "bio": data.get("bio"),
                "company": data.get("company"),
                "location": data.get("location"),
                "email": data.get("email"),
                "blog": data.get("blog"),
                "public_repos": data.get("public_repos"),
                "public_gists": data.get("public_gists"),
                "followers": data.get("followers"),
                "following": data.get("following"),
                "created_at": data.get("created_at"),
                "avatar_url": data.get("avatar_url"),
                "hireable": data.get("hireable"),
                "twitter_username": data.get("twitter_username"),
            }
    except Exception as e:
        logger.debug(f"GitHub API failed for {username}: {e}")
    return None
