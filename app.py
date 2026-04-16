"""
OSINT Analyzer Ultimate — Main Application
Flask server with API endpoints for all OSINT modules.
"""

import json
import logging
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, jsonify, Response

# Import all modules
from modules.search_engines import multi_engine_search
from modules.email_harvest import harvest_emails
from modules.phone_harvest import harvest_phones
from modules.social_profiler import extract_profiles_from_results
from modules.dns_enum import dns_enumerate
from modules.whois_lookup import whois_lookup
from modules.ssl_inspector import inspect_ssl
from modules.port_scanner import scan_ports
from modules.subdomain_finder import find_subdomains
from modules.tech_detector import detect_technologies
from modules.http_analyzer import analyze_headers
from modules.geoip_resolver import geoip_lookup
from modules.username_checker import check_username
from modules.wayback_lookup import wayback_lookup

# ─── App Setup ───────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "osint-analyzer-secret"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress noisy urllib3 warnings for unverified HTTPS
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ─── Routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main OSINT dashboard."""
    return render_template("index.html")


# ─── Main Search Endpoint ────────────────────────────────────────────────

@app.route("/search", methods=["POST"])
def search():
    """
    Main search endpoint — performs multi-engine search with automatic
    email/phone extraction and social profile detection.
    """
    query = request.form.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query is required"}), 400

    depth = int(request.form.get("depth", 3))
    enable_dorks = request.form.get("dorks", "true").lower() == "true"

    try:
        logger.info(f"Starting search: '{query}' (depth={depth}, dorks={enable_dorks})")

        # Run multi-engine search
        results = multi_engine_search(
            query,
            depth=depth,
            enable_dorks=enable_dorks,
        )

        logger.info(f"Search complete: {len(results)} results found for '{query}'")
        return jsonify(results)

    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ─── Advanced Module Endpoints ───────────────────────────────────────────

@app.route("/api/dns", methods=["POST"])
def api_dns():
    """DNS enumeration for a domain."""
    domain = request.json.get("domain", "").strip()
    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    try:
        result = dns_enumerate(domain)
        return jsonify(result)
    except Exception as e:
        logger.error(f"DNS enum error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/whois", methods=["POST"])
def api_whois():
    """WHOIS lookup for a domain."""
    domain = request.json.get("domain", "").strip()
    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    try:
        result = whois_lookup(domain)
        return jsonify(result)
    except Exception as e:
        logger.error(f"WHOIS error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ssl", methods=["POST"])
def api_ssl():
    """SSL/TLS certificate inspection."""
    hostname = request.json.get("hostname", "").strip()
    if not hostname:
        return jsonify({"error": "Hostname is required"}), 400

    port = int(request.json.get("port", 443))

    try:
        result = inspect_ssl(hostname, port=port)
        return jsonify(result)
    except Exception as e:
        logger.error(f"SSL inspection error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/ports", methods=["POST"])
def api_ports():
    """Port scanning for a host."""
    host = request.json.get("host", "").strip()
    if not host:
        return jsonify({"error": "Host is required"}), 400

    scan_type = request.json.get("scan_type", "common")

    try:
        result = scan_ports(host, scan_type=scan_type)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Port scan error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/subdomains", methods=["POST"])
def api_subdomains():
    """Subdomain discovery for a domain."""
    domain = request.json.get("domain", "").strip()
    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    enable_bruteforce = request.json.get("bruteforce", True)

    try:
        result = find_subdomains(domain, enable_bruteforce=enable_bruteforce)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Subdomain finder error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tech", methods=["POST"])
def api_tech():
    """Technology detection for a URL."""
    url = request.json.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        result = detect_technologies(url)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Tech detection error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/headers", methods=["POST"])
def api_headers():
    """HTTP header security analysis."""
    url = request.json.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        result = analyze_headers(url)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Header analysis error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/geoip", methods=["POST"])
def api_geoip():
    """GeoIP lookup for an IP or hostname."""
    target = request.json.get("target", "").strip()
    if not target:
        return jsonify({"error": "Target IP or hostname is required"}), 400

    try:
        result = geoip_lookup(target)
        return jsonify(result)
    except Exception as e:
        logger.error(f"GeoIP error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/username", methods=["POST"])
def api_username():
    """Username enumeration across 30+ platforms."""
    username = request.json.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username is required"}), 400

    try:
        result = check_username(username)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Username check error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/wayback", methods=["POST"])
def api_wayback():
    """Wayback Machine historical snapshots lookup."""
    url = request.json.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    limit = int(request.json.get("limit", 20))

    try:
        result = wayback_lookup(url, limit=limit)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Wayback error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/emails", methods=["POST"])
def api_emails():
    """Extract emails from provided search results."""
    search_results = request.json.get("results", [])
    query = request.json.get("query", "")

    try:
        result = harvest_emails(search_results, query=query)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Email harvest error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/phones", methods=["POST"])
def api_phones():
    """Extract phone numbers from provided search results."""
    search_results = request.json.get("results", [])

    try:
        result = harvest_phones(search_results)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Phone harvest error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/social", methods=["POST"])
def api_social():
    """Extract social media profiles from provided search results."""
    search_results = request.json.get("results", [])

    try:
        result = extract_profiles_from_results(search_results)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Social profiler error: {e}")
        return jsonify({"error": str(e)}), 500


# ─── Full OSINT Scan (Parallel) ─────────────────────────────────────────

@app.route("/api/full-scan", methods=["POST"])
def api_full_scan():
    """
    Run a comprehensive OSINT scan on a domain/target.
    Combines: DNS, WHOIS, SSL, Tech Detection, Headers, Subdomains, GeoIP.
    Runs all scans in parallel using ThreadPoolExecutor for speed.
    """
    target = request.json.get("target", "").strip()
    if not target:
        return jsonify({"error": "Target is required"}), 400

    results = {}
    errors = {}

    # Define all scan tasks
    scan_tasks = {
        "dns": lambda: dns_enumerate(target),
        "whois": lambda: whois_lookup(target),
        "ssl": lambda: inspect_ssl(target),
        "tech": lambda: detect_technologies(target),
        "headers": lambda: analyze_headers(target),
        "geoip": lambda: geoip_lookup(target),
    }

    # Execute all scans in parallel
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_name = {
            executor.submit(task): name
            for name, task in scan_tasks.items()
        }

        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                results[name] = future.result()
            except Exception as e:
                errors[name] = str(e)
                logger.error(f"Full scan — {name} failed: {e}")

    return jsonify({
        "target": target,
        "results": results,
        "errors": errors,
    })


# ─── Export Endpoint ─────────────────────────────────────────────────────

@app.route("/api/export", methods=["POST"])
def api_export():
    """
    Export scan results as a downloadable JSON file.
    Accepts any JSON payload and returns it as a downloadable file.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data to export"}), 400

        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        return Response(
            json_str,
            mimetype="application/json",
            headers={
                "Content-Disposition": "attachment; filename=osint_results.json"
            }
        )
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500


# ─── Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("🚀 OSINT Analyzer Ultimate starting...")
    logger.info("📡 Dashboard: http://localhost:5000")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False,
    )