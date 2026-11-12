import pyotp

def generate_mfa_secret() -> str:
    """Generate a random base32 secret for MFA."""
    return pyotp.random_base32()

def verify_mfa_code(secret: str, code: str) -> bool:
    """Verify a TOTP code against a secret."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def get_provisioning_uri(secret: str, username: str, issuer_name: str = "DragonS1") -> str:
    """Get the provisioning URI for QR code generation."""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer_name)
