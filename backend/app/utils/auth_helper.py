import os
import hmac
import hashlib
import json
import base64
import time
from typing import Optional, Dict, Any

# Secure Fallback Secret Key if not configured in environment
JWT_SECRET = os.getenv("JWT_SECRET", "devpilot-ai-custom-jwt-signing-secret-key-32890")

def hash_password(password: str) -> str:
    """
    Generate pbkdf2_hmac hash with a random salt.
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + key.hex()

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a raw password against the hashed string using constant time comparison.
    """
    try:
        salt_hex, key_hex = hashed.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False

def sign_jwt(data: Dict[str, Any], expires_in_seconds: int = 86400) -> str:
    """
    Generate a signed JWT-like base64 token with expiration.
    """
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_in_seconds
    
    # Base64 encode JSON payload
    payload_json = json.dumps(payload).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode('utf-8').rstrip("=")
    
    # Sign payload
    signature = hmac.new(JWT_SECRET.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip("=")
    
    return f"{payload_b64}.{sig_b64}"

def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify signature and decode signed token. Returns None if invalid or expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
            
        payload_b64, sig_b64 = parts[0], parts[1]
        
        # Verify signature
        signature = hmac.new(JWT_SECRET.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip("=")
        
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
            
        # Add padding back if necessary
        pad_len = 4 - (len(payload_b64) % 4)
        payload_b64_padded = payload_b64 + ("=" * (pad_len % 4))
        
        decoded_bytes = base64.urlsafe_b64decode(payload_b64_padded.encode('utf-8'))
        payload = json.loads(decoded_bytes.decode('utf-8'))
        
        if payload.get("exp", 0) < time.time():
            return None # Expired
            
        return payload
    except Exception:
        return None
