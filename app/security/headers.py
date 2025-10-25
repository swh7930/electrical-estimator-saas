from flask_talisman import Talisman

def init_security(app):
    """
    Production/staging security headers with a conservative CSP.
    Keep inline JS out of templates to avoid 'unsafe-inline'.
    """
    csp = {
        "default-src": ["'self'"],
        "script-src":  ["'self'", "https://js.stripe.com"],
        "style-src":   ["'self'", "'unsafe-inline'"],  # allow print CSS in PDF templates
        "img-src":     ["'self'", "data:", "blob:"],
        "font-src":    ["'self'", "data:"],
        "connect-src": ["'self'", "https://api.stripe.com"],
        "frame-src":   ["'self'", "https://js.stripe.com", "https://hooks.stripe.com"],
        "frame-ancestors": ["'self'"],
        "base-uri":    ["'self'"],
        "form-action": ["'self'"],
    }

    Talisman(
        app,
        content_security_policy=csp,
        force_https=True,
        strict_transport_security=True,
        session_cookie_secure=True,
        frame_options="SAMEORIGIN",
        referrer_policy="strict-origin-when-cross-origin",
    )
