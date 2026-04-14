# """
# Multi-Engine Search Module
# Searches across DuckDuckGo, Google (via dorks), and Bing simultaneously.
# Supports configurable depth and intelligent result deduplication.
# """

# import re
# import logging
# from urllib.parse import quote_plus, urlparse
# from playwright.sync_api import sync_playwright

# logger = logging.getLogger(__name__)


# # ─── Site Classification ────────────────────────────────────────────────
# SITE_CATEGORIES = {
#     "social": {
#         "Facebook": ["facebook.com", "fb.com", "fb.me"],
#         "Twitter/X": ["twitter.com", "x.com", "t.co"],
#         "LinkedIn": ["linkedin.com"],
#         "Instagram": ["instagram.com"],
#         "GitHub": ["github.com", "gist.github.com"],
#         "YouTube": ["youtube.com", "youtu.be"],
#         "TikTok": ["tiktok.com"],
#         "WhatsApp": ["whatsapp.com", "wa.me"],
#         "Snapchat": ["snapchat.com"],
#         "Telegram": ["telegram.org", "t.me", "telegram.me"],
#         "Reddit": ["reddit.com"],
#         "Pinterest": ["pinterest.com"],
#         "Discord": ["discord.com", "discord.gg"],
#         "Twitch": ["twitch.tv"],
#         "Mastodon": ["mastodon.social", "mastodon.online"],
#         "Threads": ["threads.net"],
#         "Tumblr": ["tumblr.com"],
#         "Flickr": ["flickr.com"],
#         "VK": ["vk.com"],
#         "Weibo": ["weibo.com"],
#     },
#     "professional": {
#         "LinkedIn": ["linkedin.com"],
#         "AngelList": ["angel.co", "wellfound.com"],
#         "Glassdoor": ["glassdoor.com"],
#         "Crunchbase": ["crunchbase.com"],
#         "Indeed": ["indeed.com"],
#     },
#     "dev": {
#         "GitHub": ["github.com"],
#         "GitLab": ["gitlab.com"],
#         "Bitbucket": ["bitbucket.org"],
#         "StackOverflow": ["stackoverflow.com"],
#         "HackerNews": ["news.ycombinator.com"],
#         "Dev.to": ["dev.to"],
#         "CodePen": ["codepen.io"],
#         "npm": ["npmjs.com"],
#         "PyPI": ["pypi.org"],
#     },
#     "education": {
#         "Coursera": ["coursera.org"],
#         "edX": ["edx.org"],
#         "Udemy": ["udemy.com"],
#         "Khan Academy": ["khanacademy.org"],
#         "Codecademy": ["codecademy.com"],
#         "Pluralsight": ["pluralsight.com"],
#         "Udacity": ["udacity.com"],
#         "FutureLearn": ["futurelearn.com"],
#         "Skillshare": ["skillshare.com"],
#     },
#     "news": {
#         "CNN": ["cnn.com"],
#         "BBC": ["bbc.com", "bbc.co.uk"],
#         "NYTimes": ["nytimes.com"],
#         "The Guardian": ["theguardian.com"],
#         "Reuters": ["reuters.com"],
#         "Al Jazeera": ["aljazeera.com"],
#         "Fox News": ["foxnews.com"],
#         "Washington Post": ["washingtonpost.com"],
#         "Bloomberg": ["bloomberg.com"],
#         "TechCrunch": ["techcrunch.com"],
#         "Wired": ["wired.com"],
#         "Ars Technica": ["arstechnica.com"],
#         "The Verge": ["theverge.com"],
#     },
#     "government": {
#         "Government": [".gov", ".gov.uk", ".gov.au", ".gov.ma", ".gouv.fr"],
#     },
#     "academic": {
#         "Academic": [".edu", ".ac.uk", ".ac.jp"],
#         "Google Scholar": ["scholar.google.com"],
#         "ResearchGate": ["researchgate.net"],
#         "Academia.edu": ["academia.edu"],
#     },
#     "paste_leak": {
#         "Pastebin": ["pastebin.com"],
#         "Ghostbin": ["ghostbin.co"],
#         "Hastebin": ["hastebin.com"],
#     },
#     "forum": {
#         "Reddit": ["reddit.com"],
#         "Quora": ["quora.com"],
#         "HackerNews": ["news.ycombinator.com"],
#         "4chan": ["4chan.org", "4channel.org"],
#     },
# }


# def classify_site(link, title):
#     """Classify a URL into a category and platform name."""
#     if not link:
#         return "Unknown", "Unknown"

#     link_lower = link.lower()
#     title_lower = (title or "").lower()

#     # Check all categories
#     for category, platforms in SITE_CATEGORIES.items():
#         for platform, domains in platforms.items():
#             for domain in domains:
#                 if domain in link_lower:
#                     return category, platform

#     # Email detection
#     if "@" in link_lower or any(w in title_lower for w in ["email", "mail", "e-mail"]):
#         return "contact", "Email"

#     # Phone detection
#     phone_keywords = ["phone", "call", "contact", "mobile", "tel", "+212", "+1", "+44", "+33"]
#     if any(w in title_lower for w in phone_keywords):
#         return "contact", "Phone"

#     # File type detection
#     file_extensions = {
#         ".pdf": "Document",
#         ".doc": "Document",
#         ".docx": "Document",
#         ".xls": "Spreadsheet",
#         ".xlsx": "Spreadsheet",
#         ".ppt": "Presentation",
#         ".csv": "Data File",
#         ".json": "Data File",
#         ".xml": "Data File",
#     }
#     for ext, ftype in file_extensions.items():
#         if ext in link_lower:
#             return "file", ftype

#     # Official sites
#     if any(d in link_lower for d in [".gov", ".edu", ".org"]):
#         return "official", "Official Website"

#     return "website", "General Website"


# # ─── Google Dork Queries ────────────────────────────────────────────────
# def generate_dork_queries(query):
#     """Generate Google/DuckDuckGo dork queries for deeper investigation."""
#     dorks = [
#         f'"{query}"',                           # Exact match
#         f'"{query}" site:linkedin.com',          # LinkedIn profiles
#         f'"{query}" site:facebook.com',          # Facebook profiles
#         f'"{query}" site:twitter.com OR site:x.com',  # Twitter profiles
#         f'"{query}" site:github.com',            # GitHub profiles
#         f'"{query}" filetype:pdf',               # PDF documents
#         f'"{query}" filetype:doc OR filetype:docx',  # Word documents
#         f'"{query}" filetype:xls OR filetype:xlsx',  # Spreadsheets
#         f'"{query}" site:pastebin.com',          # Paste sites
#         f'"{query}" inurl:email OR inurl:contact',  # Contact pages
#         f'"{query}" "@gmail.com" OR "@yahoo.com" OR "@hotmail.com"',  # Email addresses
#         f'"{query}" phone OR mobile OR contact OR tel',  # Phone numbers
#         f'"{query}" site:reddit.com',            # Reddit mentions
#         f'"{query}" site:medium.com',            # Medium articles
#         f'"{query}" password OR credentials OR leak',  # Credential leaks
#         f'"{query}" resume OR CV OR curriculum',  # Resumes
#     ]
#     return dorks


# # ─── DuckDuckGo Scraper ─────────────────────────────────────────────────
# def scrape_duckduckgo(query, num_pages=5, progress_callback=None):
#     """Scrape DuckDuckGo search results with configurable depth."""
#     results = []
#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             context = browser.new_context(
#                 user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#             )
#             page = context.new_page()
#             search_url = f"https://duckduckgo.com/?q={quote_plus(query)}&t=h_&ia=web"
#             page.goto(search_url, timeout=60000, wait_until="domcontentloaded")

#             for page_num in range(num_pages):
#                 if progress_callback:
#                     progress_callback(f"DuckDuckGo صفحة {page_num + 1}/{num_pages}")

#                 try:
#                     page.wait_for_selector("[data-testid='result']", timeout=15000)
#                 except Exception:
#                     logger.warning(f"No results found on DDG page {page_num + 1}")
#                     break

#                 # Extract all result links
#                 elements = page.query_selector_all("[data-testid='result']")
#                 for el in elements:
#                     try:
#                         link_el = el.query_selector("a[data-testid='result-title-a']")
#                         snippet_el = el.query_selector("[data-result='snippet']")
#                         if not link_el:
#                             link_el = el.query_selector("a")

#                         if link_el:
#                             title = link_el.inner_text().strip()
#                             link = link_el.get_attribute("href") or ""
#                             snippet = snippet_el.inner_text().strip() if snippet_el else ""
                            
#                             if link and not link.startswith("javascript"):
#                                 category, platform = classify_site(link, title)
#                                 results.append({
#                                     "title": title,
#                                     "link": link,
#                                     "snippet": snippet,
#                                     "source": "DuckDuckGo",
#                                     "category": category,
#                                     "platform": platform,
#                                 })
#                     except Exception:
#                         continue

#                 # Click "More Results" button
#                 try:
#                     more_btn = page.query_selector("button#more-results")
#                     if more_btn:
#                         more_btn.click()
#                         page.wait_for_timeout(2000)
#                     else:
#                         break
#                 except Exception:
#                     break

#             browser.close()
#     except Exception as e:
#         logger.error(f"DuckDuckGo scrape error: {e}")

#     return results


# # ─── DuckDuckGo Dorking ──────────────────────────────────────────────────
# def scrape_dorks(query, max_dorks=8, progress_callback=None):
#     """Run dork queries through DuckDuckGo for deeper results."""
#     dorks = generate_dork_queries(query)[:max_dorks]
#     all_results = []

#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             context = browser.new_context(
#                 user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#             )

#             for i, dork in enumerate(dorks):
#                 if progress_callback:
#                     progress_callback(f"Dork {i+1}/{len(dorks)}: {dork[:50]}...")

#                 page = context.new_page()
#                 try:
#                     url = f"https://duckduckgo.com/?q={quote_plus(dork)}&t=h_&ia=web"
#                     page.goto(url, timeout=30000, wait_until="domcontentloaded")

#                     try:
#                         page.wait_for_selector("[data-testid='result']", timeout=10000)
#                     except Exception:
#                         page.close()
#                         continue

#                     elements = page.query_selector_all("[data-testid='result']")
#                     for el in elements:
#                         try:
#                             link_el = el.query_selector("a[data-testid='result-title-a']")
#                             snippet_el = el.query_selector("[data-result='snippet']")
#                             if not link_el:
#                                 link_el = el.query_selector("a")
#                             if link_el:
#                                 title = link_el.inner_text().strip()
#                                 link = link_el.get_attribute("href") or ""
#                                 snippet = snippet_el.inner_text().strip() if snippet_el else ""
#                                 if link and not link.startswith("javascript"):
#                                     category, platform = classify_site(link, title)
#                                     all_results.append({
#                                         "title": title,
#                                         "link": link,
#                                         "snippet": snippet,
#                                         "source": f"Dork: {dork[:40]}",
#                                         "category": category,
#                                         "platform": platform,
#                                     })
#                         except Exception:
#                             continue
#                 except Exception as e:
#                     logger.warning(f"Dork failed: {dork} — {e}")
#                 finally:
#                     page.close()

#                 # Delay between dorks to avoid rate limiting
#                 import time
#                 time.sleep(1)

#             browser.close()
#     except Exception as e:
#         logger.error(f"Dork engine error: {e}")

#     return all_results


# # ─── Deduplication ───────────────────────────────────────────────────────
# def deduplicate_results(results):
#     """Remove duplicate results based on URL."""
#     seen = set()
#     unique = []
#     for r in results:
#         url = r.get("link", "").rstrip("/").lower()
#         domain = urlparse(url).netloc
#         if url and url not in seen:
#             seen.add(url)
#             r["domain"] = domain
#             unique.append(r)
#     return unique


# # ─── Master Search ───────────────────────────────────────────────────────
# def multi_engine_search(query, depth=5, enable_dorks=True, progress_callback=None):
#     """Run search across multiple engines and dork queries."""
#     all_results = []

#     # Standard DuckDuckGo search
#     if progress_callback:
#         progress_callback("🔍 بدء البحث في DuckDuckGo...")
#     ddg_results = scrape_duckduckgo(query, num_pages=depth, progress_callback=progress_callback)
#     all_results.extend(ddg_results)

#     # Dork-based deep search
#     if enable_dorks:
#         if progress_callback:
#             progress_callback("🕵️ بدء البحث المتقدم (Dorking)...")
#         dork_results = scrape_dorks(query, max_dorks=8, progress_callback=progress_callback)
#         all_results.extend(dork_results)

#     # Deduplicate
#     unique_results = deduplicate_results(all_results)

#     if progress_callback:
#         progress_callback(f"✅ تم العثور على {len(unique_results)} نتيجة فريدة")

#     return unique_results
