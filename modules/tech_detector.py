"""
Technology Detector Module
Detects web technologies, CMS, frameworks, and servers from HTTP headers and HTML content.
"""

import re
import logging
import requests

logger = logging.getLogger(__name__)

# Technology signatures: name -> {headers, html_patterns, meta_patterns, script_patterns}
TECH_SIGNATURES = {
    # Web Servers
    "Apache": {"headers": {"server": "apache"}, "category": "Web Server"},
    "Nginx": {"headers": {"server": "nginx"}, "category": "Web Server"},
    "IIS": {"headers": {"server": "microsoft-iis"}, "category": "Web Server"},
    "LiteSpeed": {"headers": {"server": "litespeed"}, "category": "Web Server"},
    "Caddy": {"headers": {"server": "caddy"}, "category": "Web Server"},
    "Cloudflare": {"headers": {"server": "cloudflare"}, "category": "CDN"},

    # CMS
    "WordPress": {
        "html": [r'wp-content/', r'wp-includes/', r'wp-json', r'/xmlrpc\.php'],
        "meta": [r'WordPress'],
        "category": "CMS",
    },
    "Drupal": {
        "html": [r'Drupal\.settings', r'sites/default/files', r'drupal\.js'],
        "headers": {"x-generator": "drupal"},
        "category": "CMS",
    },
    "Joomla": {
        "html": [r'/media/jui/', r'/components/com_', r'Joomla!'],
        "meta": [r'Joomla'],
        "category": "CMS",
    },
    "Shopify": {
        "html": [r'cdn\.shopify\.com', r'shopify\.com', r'Shopify\.theme'],
        "category": "E-commerce",
    },
    "Wix": {
        "html": [r'wix\.com', r'_wixCIDX', r'X-Wix-'],
        "category": "Website Builder",
    },
    "Squarespace": {
        "html": [r'squarespace\.com', r'squarespace-cdn\.com'],
        "category": "Website Builder",
    },

    # JavaScript Frameworks
    "React": {
        "html": [r'react\.production\.min\.js', r'__NEXT_DATA__', r'_reactRootContainer', r'data-reactroot'],
        "category": "JS Framework",
    },
    "Next.js": {
        "html": [r'__NEXT_DATA__', r'_next/static', r'/_next/'],
        "headers": {"x-powered-by": "next.js"},
        "category": "JS Framework",
    },
    "Vue.js": {
        "html": [r'vue\.js', r'vue\.min\.js', r'v-cloak', r'data-v-', r'__vue__'],
        "category": "JS Framework",
    },
    "Angular": {
        "html": [r'ng-version', r'angular\.js', r'ng-app', r'ng-controller'],
        "category": "JS Framework",
    },
    "Svelte": {
        "html": [r'svelte', r'__svelte'],
        "category": "JS Framework",
    },
    "jQuery": {
        "html": [r'jquery\.js', r'jquery\.min\.js', r'jquery-\d'],
        "category": "JS Library",
    },

    # Backend
    "PHP": {
        "headers": {"x-powered-by": "php"},
        "html": [r'\.php\b'],
        "category": "Backend",
    },
    "ASP.NET": {
        "headers": {"x-powered-by": "asp.net", "x-aspnet-version": ""},
        "category": "Backend",
    },
    "Express.js": {
        "headers": {"x-powered-by": "express"},
        "category": "Backend",
    },
    "Django": {
        "headers": {"x-frame-options": "deny"},
        "html": [r'csrfmiddlewaretoken', r'django'],
        "category": "Backend",
    },
    "Ruby on Rails": {
        "headers": {"x-powered-by": "phusion passenger"},
        "html": [r'csrf-token', r'ruby'],
        "category": "Backend",
    },
    "Laravel": {
        "html": [r'laravel', r'XSRF-TOKEN'],
        "category": "Backend",
    },

    # Analytics & Marketing
    "Google Analytics": {
        "html": [r'google-analytics\.com', r'googletagmanager\.com', r'ga\.js', r'gtag', r'UA-\d+'],
        "category": "Analytics",
    },
    "Google Tag Manager": {
        "html": [r'googletagmanager\.com/gtm\.js', r'GTM-\w+'],
        "category": "Analytics",
    },
    "Facebook Pixel": {
        "html": [r'connect\.facebook\.net', r'fbq\(', r'facebook\.com/tr'],
        "category": "Analytics",
    },
    "Hotjar": {
        "html": [r'hotjar\.com', r'static\.hotjar\.com'],
        "category": "Analytics",
    },

    # Security
    "reCAPTCHA": {
        "html": [r'google\.com/recaptcha', r'g-recaptcha'],
        "category": "Security",
    },
    "Cloudflare": {
        "headers": {"cf-ray": "", "cf-cache-status": ""},
        "html": [r'cloudflare', r'cdn-cgi'],
        "category": "CDN/Security",
    },

    # Hosting
    "AWS": {
        "headers": {"server": "amazons3", "x-amz-": ""},
        "html": [r'amazonaws\.com', r's3\.amazonaws'],
        "category": "Cloud",
    },
    "Google Cloud": {
        "html": [r'googleapis\.com', r'storage\.googleapis'],
        "category": "Cloud",
    },
    "Vercel": {
        "headers": {"x-vercel-id": "", "server": "vercel"},
        "category": "Hosting",
    },
    "Netlify": {
        "headers": {"server": "netlify"},
        "category": "Hosting",
    },
    "Heroku": {
        "headers": {"via": "heroku"},
        "category": "Hosting",
    },
}


def detect_technologies(url, progress_callback=None):
    """
    Detect technologies used by a website.
    
    Args:
        url: Target URL
        progress_callback: Progress callback function
    
    Returns:
        Dict with detected technologies grouped by category
    """
    if progress_callback:
        progress_callback(f"🔧 كشف التقنيات لـ {url}...")

    if not url.startswith("http"):
        url = f"https://{url}"

    result = {
        "url": url,
        "technologies": [],
        "categories": {},
        "headers": {},
        "error": None,
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, timeout=15, headers=headers, verify=False, allow_redirects=True)

        # Store response headers
        result["headers"] = dict(resp.headers)
        result["status_code"] = resp.status_code
        result["final_url"] = resp.url
        html = resp.text.lower()
        resp_headers = {k.lower(): v.lower() for k, v in resp.headers.items()}

        for tech_name, tech_info in TECH_SIGNATURES.items():
            detected = False

            # Check headers
            if "headers" in tech_info:
                for header_name, header_value in tech_info["headers"].items():
                    if header_name in resp_headers:
                        if not header_value or header_value in resp_headers[header_name]:
                            detected = True
                            break

            # Check HTML patterns
            if not detected and "html" in tech_info:
                for pattern in tech_info["html"]:
                    if re.search(pattern.lower(), html):
                        detected = True
                        break

            # Check meta tags
            if not detected and "meta" in tech_info:
                for pattern in tech_info["meta"]:
                    if re.search(f'<meta[^>]*{pattern.lower()}[^>]*>', html):
                        detected = True
                        break

            if detected:
                category = tech_info.get("category", "Other")
                tech_entry = {
                    "name": tech_name,
                    "category": category,
                }
                result["technologies"].append(tech_entry)

                if category not in result["categories"]:
                    result["categories"][category] = []
                result["categories"][category].append(tech_name)

        # Extract additional info
        # Server version
        if "server" in resp_headers:
            result["server"] = resp_headers["server"]

        # Security headers analysis
        security_headers = {
            "strict-transport-security": "HSTS",
            "content-security-policy": "CSP",
            "x-frame-options": "X-Frame-Options",
            "x-content-type-options": "X-Content-Type-Options",
            "x-xss-protection": "X-XSS-Protection",
            "referrer-policy": "Referrer-Policy",
            "permissions-policy": "Permissions-Policy",
            "feature-policy": "Feature-Policy",
        }
        
        result["security_headers"] = {}
        for header, name in security_headers.items():
            result["security_headers"][name] = {
                "present": header in resp_headers,
                "value": resp_headers.get(header, None),
            }

        # Count security headers present
        present_count = sum(1 for v in result["security_headers"].values() if v["present"])
        total_headers = len(security_headers)
        result["security_score"] = round((present_count / total_headers) * 100)

        if progress_callback:
            progress_callback(f"✅ اكتُشفت {len(result['technologies'])} تقنية")

    except Exception as e:
        result["error"] = str(e)
        if progress_callback:
            progress_callback(f"⚠️ فشل كشف التقنيات: {e}")

    return result
