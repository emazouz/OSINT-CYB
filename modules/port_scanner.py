"""
Port Scanner Module
Scans common ports on a target host to discover running services.
⚠️ Use only on targets you own or have authorization to scan.
"""

import logging
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Top 100 most common ports with service descriptions
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPC", 135: "MSRPC", 139: "NetBIOS",
    143: "IMAP", 443: "HTTPS", 445: "SMB", 465: "SMTPS", 587: "SMTP-SUB",
    993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
    2049: "NFS", 2082: "cPanel", 2083: "cPanel-SSL",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
    5985: "WinRM", 6379: "Redis", 6443: "K8s-API",
    8000: "HTTP-Alt", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt",
    8888: "HTTP-Alt2", 9090: "Prometheus", 9200: "Elasticsearch",
    9300: "ES-Transport", 10000: "Webmin", 27017: "MongoDB",
    27018: "MongoDB-Shard", 5672: "RabbitMQ", 15672: "RabbitMQ-Mgmt",
    11211: "Memcached", 50000: "SAP",
}

# Extended port list for deeper scans
EXTENDED_PORTS = {
    **COMMON_PORTS,
    20: "FTP-Data", 69: "TFTP", 88: "Kerberos", 161: "SNMP",
    162: "SNMP-Trap", 389: "LDAP", 636: "LDAPS", 873: "Rsync",
    1080: "SOCKS", 1194: "OpenVPN", 1723: "PPTP", 1883: "MQTT",
    2181: "ZooKeeper", 3000: "Grafana/Dev", 4443: "Pharos",
    5000: "Docker-Registry", 5601: "Kibana", 7001: "WebLogic",
    8081: "HTTP-Alt3", 8082: "HTTP-Alt4", 8444: "HTTPS-Alt2",
    8880: "CDDBP", 8983: "Solr", 9000: "SonarQube",
    9092: "Kafka", 9418: "Git", 9999: "IANA",
    1025: "NFS-Alt", 1026: "DCOM", 1027: "IIS",
    2222: "SSH-Alt", 4444: "Metasploit", 5555: "ADB",
    6000: "X11", 6666: "IRC", 6667: "IRC-Alt",
    7000: "Cassandra", 7070: "RTSP-Alt", 7443: "Oracle-SSL",
    8008: "HTTP-Alt5", 8090: "HTTP-Alt6",
}


def scan_port(host, port, timeout=2):
    """Scan a single port on a host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def grab_banner(host, port, timeout=3):
    """Attempt to grab the service banner from an open port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        # Send a probe for HTTP ports
        if port in (80, 8080, 8000, 8888, 443, 8443):
            sock.send(b"HEAD / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
        else:
            sock.send(b"\r\n")
        
        banner = sock.recv(1024).decode("utf-8", errors="ignore").strip()
        sock.close()
        return banner[:200] if banner else None
    except Exception:
        return None


def scan_ports(host, scan_type="common", max_workers=50, timeout=2, progress_callback=None):
    """
    Scan ports on a target host.
    
    Args:
        host: Target hostname or IP
        scan_type: "common" (top 40) or "extended" (top 80)
        max_workers: Number of concurrent scan threads
        timeout: Connection timeout in seconds
        progress_callback: Progress callback function
    
    Returns:
        Dict with open ports, services, and scan statistics
    """
    ports_to_scan = COMMON_PORTS if scan_type == "common" else EXTENDED_PORTS

    if progress_callback:
        progress_callback(f"🔌 فحص {len(ports_to_scan)} منفذ على {host}...")

    # Resolve hostname to IP
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return {"error": f"Cannot resolve host: {host}", "host": host, "open_ports": []}

    open_ports = []
    total = len(ports_to_scan)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(scan_port, ip, port, timeout): (port, service)
            for port, service in ports_to_scan.items()
        }

        for i, future in enumerate(as_completed(futures)):
            port, service = futures[future]
            try:
                is_open = future.result()
                if is_open:
                    # Try banner grab
                    banner = grab_banner(ip, port)
                    open_ports.append({
                        "port": port,
                        "service": service,
                        "state": "open",
                        "banner": banner,
                    })
                    if progress_callback:
                        progress_callback(f"🟢 المنفذ {port} ({service}) مفتوح!")
            except Exception:
                pass

            if progress_callback and (i + 1) % 20 == 0:
                progress_callback(f"🔌 فحص {i+1}/{total} ({len(open_ports)} مفتوح)")

    # Sort by port number
    open_ports.sort(key=lambda x: x["port"])

    # Risk assessment
    high_risk_ports = {21, 23, 445, 3389, 5900, 1433, 3306, 5432, 27017, 6379, 11211}
    risk_ports = [p for p in open_ports if p["port"] in high_risk_ports]

    if progress_callback:
        progress_callback(f"✅ اكتمل الفحص: {len(open_ports)} منفذ مفتوح")

    return {
        "host": host,
        "ip": ip,
        "open_ports": open_ports,
        "total_scanned": total,
        "open_count": len(open_ports),
        "high_risk_ports": risk_ports,
        "risk_level": "HIGH" if risk_ports else ("MEDIUM" if len(open_ports) > 5 else "LOW"),
    }
