# """
# Subdomain Finder Module
# Discovers subdomains using crt.sh certificate transparency logs and DNS brute-force.
# """

# import logging
# import requests
# import dns.resolver
# from concurrent.futures import ThreadPoolExecutor, as_completed

# logger = logging.getLogger(__name__)

# # Common subdomain wordlist
# COMMON_SUBDOMAINS = [
#     "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "ns2",
#     "ns3", "ns4", "dns", "dns1", "dns2", "api", "dev", "staging", "stage",
#     "test", "testing", "beta", "alpha", "demo", "app", "apps", "admin",
#     "portal", "dashboard", "panel", "login", "secure", "vpn", "remote",
#     "gateway", "proxy", "cdn", "static", "assets", "img", "images", "media",
#     "video", "files", "download", "upload", "docs", "doc", "help", "support",
#     "forum", "community", "blog", "news", "shop", "store", "pay", "payment",
#     "billing", "checkout", "cart", "order", "orders", "tracking", "status",
#     "health", "monitor", "monitoring", "grafana", "prometheus", "kibana",
#     "elastic", "elasticsearch", "logstash", "jenkins", "ci", "cd", "git",
#     "gitlab", "github", "bitbucket", "jira", "confluence", "wiki",
#     "db", "database", "mysql", "postgres", "postgresql", "mongo", "mongodb",
#     "redis", "cache", "memcached", "rabbit", "rabbitmq", "queue", "mq",
#     "s3", "storage", "backup", "bak", "old", "new", "v1", "v2", "v3",
#     "internal", "intranet", "extranet", "corp", "corporate", "office",
#     "exchange", "owa", "autodiscover", "mx", "mx1", "mx2",
#     "m", "mobile", "wap", "iphone", "android",
#     "search", "analytics", "stats", "track", "tracking",
#     "cron", "task", "job", "worker", "queue",
#     "sandbox", "preview", "canary", "edge",
#     "sso", "auth", "oauth", "identity", "id",
#     "ws", "websocket", "socket", "realtime",
#     "graphql", "rest", "rpc", "grpc",
#     "smtp", "imap", "pop3", "caldav", "carddav",
#     "cpanel", "plesk", "whm", "webmin",
# ]


# def query_crt_sh(domain, progress_callback=None):
#     """Query crt.sh certificate transparency logs for subdomains."""
#     subdomains = set()
#     if progress_callback:
#         progress_callback(f"🔎 فحص شهادات SSL لـ {domain}...")

#     try:
#         url = f"https://crt.sh/?q=%.{domain}&output=json"
#         resp = requests.get(url, timeout=30)
#         if resp.status_code == 200:
#             data = resp.json()
#             for entry in data:
#                 name = entry.get("name_value", "")
#                 # Handle wildcard and multi-value entries
#                 for sub in name.split("\n"):
#                     sub = sub.strip().lower()
#                     sub = sub.lstrip("*.")
#                     if sub.endswith(f".{domain}") or sub == domain:
#                         subdomains.add(sub)

#         if progress_callback:
#             progress_callback(f"✅ crt.sh: {len(subdomains)} نطاق فرعي")

#     except Exception as e:
#         logger.error(f"crt.sh query failed: {e}")
#         if progress_callback:
#             progress_callback(f"⚠️ crt.sh فشل: {e}")

#     return subdomains


# def dns_bruteforce_single(subdomain, domain):
#     """Check if a single subdomain resolves."""
#     fqdn = f"{subdomain}.{domain}"
#     try:
#         resolver = dns.resolver.Resolver()
#         resolver.timeout = 3
#         resolver.lifetime = 3
#         answers = resolver.resolve(fqdn, "A")
#         ips = [str(r) for r in answers]
#         return {"subdomain": fqdn, "ips": ips, "exists": True}
#     except Exception:
#         return {"subdomain": fqdn, "exists": False}


# def dns_bruteforce(domain, wordlist=None, max_workers=20, progress_callback=None):
#     """Brute-force subdomains using DNS resolution."""
#     if wordlist is None:
#         wordlist = COMMON_SUBDOMAINS

#     if progress_callback:
#         progress_callback(f"🔨 Brute-force DNS: {len(wordlist)} كلمة...")

#     found = []
#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         futures = {
#             executor.submit(dns_bruteforce_single, sub, domain): sub
#             for sub in wordlist
#         }

#         for i, future in enumerate(as_completed(futures)):
#             result = future.result()
#             if result["exists"]:
#                 found.append(result)
#             if progress_callback and (i + 1) % 25 == 0:
#                 progress_callback(f"🔨 DNS Brute: {i+1}/{len(wordlist)} ({len(found)} وُجد)")

#     return found


# def find_subdomains(domain, enable_bruteforce=True, progress_callback=None):
#     """
#     Discover subdomains using multiple methods.
    
#     Args:
#         domain: Target domain
#         enable_bruteforce: Whether to run DNS brute-force
#         progress_callback: Progress callback function
    
#     Returns:
#         Dict with discovered subdomains and metadata
#     """
#     all_subdomains = {}

#     # Method 1: crt.sh certificate transparency
#     crt_subs = query_crt_sh(domain, progress_callback)
#     for sub in crt_subs:
#         all_subdomains[sub] = {
#             "subdomain": sub,
#             "source": "crt.sh",
#             "ips": [],
#         }

#     # Method 2: DNS brute-force
#     if enable_bruteforce:
#         brute_results = dns_bruteforce(domain, progress_callback=progress_callback)
#         for result in brute_results:
#             sub = result["subdomain"]
#             if sub not in all_subdomains:
#                 all_subdomains[sub] = {
#                     "subdomain": sub,
#                     "source": "dns_bruteforce",
#                     "ips": result.get("ips", []),
#                 }
#             else:
#                 all_subdomains[sub]["ips"] = result.get("ips", [])

#     # Resolve IPs for crt.sh subdomains that don't have IPs yet
#     if progress_callback:
#         progress_callback("🔍 حل عناوين IP...")

#     resolver = dns.resolver.Resolver()
#     resolver.timeout = 3
#     resolver.lifetime = 3
#     for sub_name, sub_info in all_subdomains.items():
#         if not sub_info["ips"]:
#             try:
#                 answers = resolver.resolve(sub_name, "A")
#                 sub_info["ips"] = [str(r) for r in answers]
#             except Exception:
#                 pass

#     if progress_callback:
#         progress_callback(f"✅ تم اكتشاف {len(all_subdomains)} نطاق فرعي")

#     return {
#         "domain": domain,
#         "subdomains": list(all_subdomains.values()),
#         "total_found": len(all_subdomains),
#         "unique_ips": list(set(
#             ip for sub in all_subdomains.values() for ip in sub.get("ips", [])
#         )),
#     }
