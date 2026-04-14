# """
# SSL/TLS Certificate Inspector Module
# Inspects SSL certificates for domains — issuer, expiry, SANs, protocol support.
# """

# import ssl
# import socket
# import logging
# from datetime import datetime

# logger = logging.getLogger(__name__)


# def inspect_ssl(hostname, port=443, progress_callback=None):
#     """
#     Inspect the SSL/TLS certificate for a hostname.
    
#     Args:
#         hostname: Target hostname
#         port: Target port (default 443)
#         progress_callback: Progress callback function
    
#     Returns:
#         Dict with certificate details, validity, and security analysis
#     """
#     if progress_callback:
#         progress_callback(f"🔐 فحص شهادة SSL لـ {hostname}...")

#     result = {
#         "hostname": hostname,
#         "port": port,
#         "has_ssl": False,
#         "issuer": None,
#         "subject": None,
#         "serial_number": None,
#         "version": None,
#         "not_before": None,
#         "not_after": None,
#         "days_remaining": None,
#         "is_expired": None,
#         "is_self_signed": False,
#         "san": [],
#         "signature_algorithm": None,
#         "protocol": None,
#         "cipher": None,
#         "key_size": None,
#         "ocsp": [],
#         "crl": [],
#         "error": None,
#     }

#     try:
#         # Create SSL context
#         context = ssl.create_default_context()
        
#         # Connect and get certificate
#         conn = context.wrap_socket(
#             socket.socket(socket.AF_INET, socket.SOCK_STREAM),
#             server_hostname=hostname
#         )
#         conn.settimeout(10)
#         conn.connect((hostname, port))

#         cert = conn.getpeercert()
#         cipher_info = conn.cipher()
#         protocol = conn.version()

#         result["has_ssl"] = True
#         result["protocol"] = protocol

#         # Cipher information
#         if cipher_info:
#             result["cipher"] = {
#                 "name": cipher_info[0],
#                 "protocol": cipher_info[1],
#                 "bits": cipher_info[2],
#             }
#             result["key_size"] = cipher_info[2]

#         # Subject
#         if cert.get("subject"):
#             subject_dict = {}
#             for item in cert["subject"]:
#                 for key, value in item:
#                     subject_dict[key] = value
#             result["subject"] = subject_dict

#         # Issuer
#         if cert.get("issuer"):
#             issuer_dict = {}
#             for item in cert["issuer"]:
#                 for key, value in item:
#                     issuer_dict[key] = value
#             result["issuer"] = issuer_dict

#             # Check self-signed
#             if result["subject"] and result["issuer"]:
#                 if result["subject"].get("commonName") == result["issuer"].get("commonName"):
#                     result["is_self_signed"] = True

#         # Serial number
#         result["serial_number"] = cert.get("serialNumber")
#         result["version"] = cert.get("version")

#         # Validity dates
#         not_before = cert.get("notBefore")
#         not_after = cert.get("notAfter")

#         if not_before:
#             nb = datetime.strptime(not_before, "%b %d %H:%M:%S %Y %Z")
#             result["not_before"] = nb.isoformat()

#         if not_after:
#             na = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
#             result["not_after"] = na.isoformat()
#             result["days_remaining"] = (na - datetime.utcnow()).days
#             result["is_expired"] = result["days_remaining"] < 0

#         # Subject Alternative Names
#         san_entries = cert.get("subjectAltName", [])
#         result["san"] = [value for _, value in san_entries]

#         # OCSP and CRL
#         result["ocsp"] = list(cert.get("OCSP", []))
#         result["crl"] = list(cert.get("crlDistributionPoints", []))

#         # Signature algorithm (from cert if available)
#         # Note: getpeercert() doesn't expose this directly, but we can try
#         # to get it from the binary cert
#         try:
#             bin_cert = conn.getpeercert(binary_form=True)
#             import hashlib
#             result["fingerprint_sha256"] = hashlib.sha256(bin_cert).hexdigest()
#             result["fingerprint_sha1"] = hashlib.sha1(bin_cert).hexdigest()
#         except Exception:
#             pass

#         conn.close()

#         # Security assessment
#         warnings = []
        
#         if result["is_expired"]:
#             warnings.append("⛔ الشهادة منتهية الصلاحية!")
#         elif result["days_remaining"] is not None and result["days_remaining"] < 30:
#             warnings.append(f"⚠️ الشهادة ستنتهي خلال {result['days_remaining']} يوم")
        
#         if result["is_self_signed"]:
#             warnings.append("⚠️ شهادة ذاتية التوقيع (Self-Signed)")
        
#         if result["key_size"] and result["key_size"] < 128:
#             warnings.append(f"⚠️ حجم المفتاح ضعيف: {result['key_size']} بت")
        
#         if protocol and "TLSv1.0" in protocol:
#             warnings.append("⚠️ بروتوكول TLS 1.0 قديم وغير آمن")
#         elif protocol and "TLSv1.1" in protocol:
#             warnings.append("⚠️ بروتوكول TLS 1.1 قديم")
        
#         result["warnings"] = warnings
#         result["ssl_grade"] = _calculate_ssl_grade(result)

#         if progress_callback:
#             progress_callback(f"✅ SSL Grade: {result['ssl_grade']} — {len(result['san'])} SANs")

#     except ssl.SSLCertVerificationError as e:
#         result["error"] = f"SSL Verification Error: {e}"
#         result["has_ssl"] = True  # Has SSL but invalid
#         if progress_callback:
#             progress_callback(f"⚠️ خطأ في التحقق من SSL: {e}")
#     except ConnectionRefusedError:
#         result["error"] = "Connection refused (port may be closed)"
#         if progress_callback:
#             progress_callback(f"⚠️ الاتصال مرفوض على المنفذ {port}")
#     except socket.timeout:
#         result["error"] = "Connection timed out"
#         if progress_callback:
#             progress_callback(f"⚠️ انتهت مهلة الاتصال")
#     except Exception as e:
#         result["error"] = str(e)
#         logger.error(f"SSL inspection failed for {hostname}: {e}")
#         if progress_callback:
#             progress_callback(f"⚠️ فشل فحص SSL: {e}")

#     return result


# def _calculate_ssl_grade(result):
#     """Calculate an SSL security grade."""
#     score = 100

#     if result.get("is_expired"):
#         return "F"
#     if result.get("is_self_signed"):
#         score -= 30
#     if result.get("days_remaining") is not None and result["days_remaining"] < 30:
#         score -= 15
#     if result.get("key_size") and result["key_size"] < 128:
#         score -= 25
#     if result.get("protocol"):
#         if "TLSv1.0" in result["protocol"]:
#             score -= 30
#         elif "TLSv1.1" in result["protocol"]:
#             score -= 15

#     if score >= 90:
#         return "A+"
#     elif score >= 80:
#         return "A"
#     elif score >= 70:
#         return "B"
#     elif score >= 60:
#         return "C"
#     elif score >= 40:
#         return "D"
#     else:
#         return "F"
