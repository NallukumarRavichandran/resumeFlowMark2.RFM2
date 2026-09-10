import urllib.request
import json
import random
import string
import time

class TempMailService:
    """
    Provides real disposable temporary email addresses using public temp-mail APIs
    (such as Mail.tm and 1secmail) with fallback to verified disposable domain patterns.
    """
    
    @staticmethod
    def _random_str(length=8):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    @classmethod
    def generate_account(cls):
        """
        Creates a new temporary mail inbox.
        Returns: dict with { 'email': str, 'password': str, 'provider': str, 'token': str|None }
        """
        # Try Mail.tm API first (live, real domains)
        try:
            domain_req = urllib.request.Request("https://api.mail.tm/domains", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(domain_req, timeout=5) as resp:
                domains_data = json.loads(resp.read().decode('utf-8'))
                domains = domains_data.get('hydra:member', [])
                for domain_entry in domains[:5]:
                    domain = domain_entry['domain']
                    username = f"user_{cls._random_str(8)}"
                    email = f"{username}@{domain}"
                    password = f"P@ss{cls._random_str(6)}1"
                    reg_payload = json.dumps({"address": email, "password": password}).encode('utf-8')
                    reg_req = urllib.request.Request(
                        "https://api.mail.tm/accounts",
                        data=reg_payload,
                        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
                    )
                    try:
                        with urllib.request.urlopen(reg_req, timeout=5) as reg_resp:
                            if reg_resp.status not in (200, 201):
                                continue
                        auth_payload = json.dumps({"address": email, "password": password}).encode('utf-8')
                        auth_req = urllib.request.Request(
                            "https://api.mail.tm/token",
                            data=auth_payload,
                            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
                        )
                        with urllib.request.urlopen(auth_req, timeout=5) as auth_resp:
                            token_data = json.loads(auth_resp.read().decode('utf-8'))
                        return {
                            "email": email,
                            "password": password,
                            "provider": "mail.tm",
                            "token": token_data.get('token')
                        }
                    except Exception:
                        continue
        except Exception:
            pass

        # Try 1secmail API fallback
        try:
            req = urllib.request.Request(
                "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1",
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data and isinstance(data, list):
                    email = data[0]
                    password = f"P@ss{cls._random_str(6)}1"
                    return {
                        "email": email,
                        "password": password,
                        "provider": "1secmail",
                        "token": None
                    }
        except Exception:
            pass

        raise RuntimeError("No usable temporary-mail provider is currently available.")

    @classmethod
    def check_messages(cls, email_account):
        """Checks for incoming emails if token is available"""
        token = email_account.get("token")
        if not token:
            return []
        try:
            req = urllib.request.Request(
                "https://api.mail.tm/messages",
                headers={'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data.get('hydra:member', [])
        except Exception:
            return []
