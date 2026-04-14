"""
HTTP Header Analyzer Module
Analyzes HTTP headers for security misconfigurations and information disclosure.
"""

import logging
import requests

logger = logging.getLogger(__name__)

# Security headers to check and their descriptions
SECURITY_HEADERS = {
    "strict-transport-security": {
        "name": "HSTS (Strict-Transport-Security)",
        "description": "يفرض استخدام HTTPS ويمنع هجمات تخفيض البروتوكول",
        "severity": "HIGH",
        "recommendation": "أضف: Strict-Transport-Security: max-age=31536000; includeSubDomains",
    },
    "content-security-policy": {
        "name": "CSP (Content-Security-Policy)",
        "description": "يمنع هجمات XSS وحقن البيانات",
        "severity": "HIGH",
        "recommendation": "أضف سياسة CSP صارمة تحدد مصادر المحتوى المسموح بها",
    },
    "x-frame-options": {
        "name": "X-Frame-Options",
        "description": "يمنع تضمين الصفحة في iframe (حماية من Clickjacking)",
        "severity": "MEDIUM",
        "recommendation": "أضف: X-Frame-Options: DENY أو SAMEORIGIN",
    },
    "x-content-type-options": {
        "name": "X-Content-Type-Options",
        "description": "يمنع المتصفح من تخمين نوع المحتوى",
        "severity": "MEDIUM",
        "recommendation": "أضف: X-Content-Type-Options: nosniff",
    },
    "x-xss-protection": {
        "name": "X-XSS-Protection",
        "description": "يفعّل حماية XSS المدمجة في المتصفح",
        "severity": "LOW",
        "recommendation": "أضف: X-XSS-Protection: 1; mode=block",
    },
    "referrer-policy": {
        "name": "Referrer-Policy",
        "description": "يتحكم في معلومات المرجع المرسلة مع الطلبات",
        "severity": "LOW",
        "recommendation": "أضف: Referrer-Policy: strict-origin-when-cross-origin",
    },
    "permissions-policy": {
        "name": "Permissions-Policy",
        "description": "يتحكم في ميزات المتصفح المتاحة للصفحة",
        "severity": "MEDIUM",
        "recommendation": "حدد الأذونات المطلوبة فقط",
    },
    "x-permitted-cross-domain-policies": {
        "name": "X-Permitted-Cross-Domain-Policies",
        "description": "يتحكم في سياسات Flash/PDF عبر النطاقات",
        "severity": "LOW",
        "recommendation": "أضف: X-Permitted-Cross-Domain-Policies: none",
    },
}

# Headers that may leak sensitive information
INFORMATION_DISCLOSURE_HEADERS = [
    "server", "x-powered-by", "x-aspnet-version", "x-aspnetmvc-version",
    "x-generator", "x-drupal-cache", "x-varnish", "via",
    "x-runtime", "x-version", "x-backend-server",
]


def analyze_headers(url, progress_callback=None):
    """
    Perform comprehensive HTTP header security analysis.
    
    Args:
        url: Target URL to analyze
        progress_callback: Progress callback function
    
    Returns:
        Dict with security analysis, scores, and recommendations
    """
    if progress_callback:
        progress_callback(f"🔒 تحليل ترويسات HTTP لـ {url}...")

    if not url.startswith("http"):
        url = f"https://{url}"

    result = {
        "url": url,
        "status_code": None,
        "all_headers": {},
        "security_headers": [],
        "missing_headers": [],
        "information_disclosure": [],
        "cookies_analysis": [],
        "security_score": 0,
        "grade": "F",
        "recommendations": [],
        "error": None,
    }

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, timeout=15, headers=headers, verify=False, allow_redirects=True)
        result["status_code"] = resp.status_code
        result["all_headers"] = dict(resp.headers)
        result["final_url"] = resp.url

        resp_headers_lower = {k.lower(): v for k, v in resp.headers.items()}

        # Check security headers
        present_count = 0
        for header_key, header_info in SECURITY_HEADERS.items():
            if header_key in resp_headers_lower:
                present_count += 1
                result["security_headers"].append({
                    "header": header_info["name"],
                    "value": resp_headers_lower[header_key],
                    "status": "present",
                    "severity": header_info["severity"],
                })
            else:
                result["missing_headers"].append({
                    "header": header_info["name"],
                    "description": header_info["description"],
                    "severity": header_info["severity"],
                    "recommendation": header_info["recommendation"],
                    "status": "missing",
                })
                result["recommendations"].append({
                    "severity": header_info["severity"],
                    "header": header_info["name"],
                    "fix": header_info["recommendation"],
                })

        # Check information disclosure
        for header_key in INFORMATION_DISCLOSURE_HEADERS:
            if header_key in resp_headers_lower:
                result["information_disclosure"].append({
                    "header": header_key,
                    "value": resp_headers_lower[header_key],
                    "risk": "يكشف معلومات عن الخادم/التقنيات المستخدمة",
                })

        # Analyze cookies
        if "set-cookie" in resp_headers_lower:
            cookies = resp.headers.get("Set-Cookie", "")
            cookie_flags = {
                "Secure": "secure" in cookies.lower(),
                "HttpOnly": "httponly" in cookies.lower(),
                "SameSite": "samesite" in cookies.lower(),
            }
            result["cookies_analysis"].append({
                "raw": cookies[:200],
                "flags": cookie_flags,
                "issues": [
                    f"⚠️ Cookie بدون علامة {flag}"
                    for flag, present in cookie_flags.items()
                    if not present
                ],
            })

        # Calculate security score
        total_headers = len(SECURITY_HEADERS)
        score = round((present_count / total_headers) * 100)

        # Penalize information disclosure
        score -= len(result["information_disclosure"]) * 5
        score = max(0, min(100, score))
        result["security_score"] = score

        # Assign grade
        if score >= 90:
            result["grade"] = "A+"
        elif score >= 80:
            result["grade"] = "A"
        elif score >= 70:
            result["grade"] = "B"
        elif score >= 60:
            result["grade"] = "C"
        elif score >= 40:
            result["grade"] = "D"
        else:
            result["grade"] = "F"

        if progress_callback:
            progress_callback(f"✅ درجة الأمان: {result['grade']} ({score}%)")

    except Exception as e:
        result["error"] = str(e)
        if progress_callback:
            progress_callback(f"⚠️ فشل تحليل الترويسات: {e}")

    return result
