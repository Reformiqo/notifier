"""Low-level client for the WuzAPI WhatsApp gateway.

WuzAPI (https://github.com/asternic/wuzapi) is a REST server built on top of the
`whatsmeow` Go library. It replaces the old Evolution API integration.

Auth model (this differs fundamentally from Evolution API):

* Normal endpoints authenticate with a per-session ``Token`` header. Each
  WhatsApp Instance stores its own token in ``WhatsApp Instance.token``.
* Admin endpoints (``/admin/**``) authenticate with the ``Authorization`` header
  carrying the WuzAPI admin token (``WUZAPI_ADMIN_TOKEN`` on the server), which we
  store in ``WhatsApp Settings.api_token``.

Settings mapping:
    WhatsApp Settings.base_url   -> WuzAPI base URL (e.g. http://127.0.0.1:8080)
    WhatsApp Settings.api_token  -> WuzAPI admin token
    WhatsApp Instance.token      -> per-session WuzAPI user token
"""

from urllib.parse import quote

import frappe
import requests

REQUEST_TIMEOUT = 30
DEFAULT_EVENTS = "All"
SETTINGS = "WhatsApp Settings"


# ---------------------------------------------------------------------------
# Settings / identity helpers
# ---------------------------------------------------------------------------

def get_base_url():
    url = frappe.db.get_single_value(SETTINGS, "base_url")
    return (url or "").rstrip("/")


def get_admin_token():
    return frappe.db.get_single_value(SETTINGS, "api_token")


def instance_token(instance_name):
    """Per-session WuzAPI token stored on a WhatsApp Instance."""
    return frappe.db.get_value("WhatsApp Instance", instance_name, "token")


def webhook_url_for(instance_name):
    """Public URL WuzAPI should POST events to for a given instance.

    The instance name is passed as a query param so the webhook handler knows
    which WhatsApp Instance an event belongs to.
    """
    return (
        f"{frappe.utils.get_url()}/api/method/notifier.webhook.update_instance"
        f"?instance={quote(instance_name)}"
    )


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

def _request(method, path, token=None, admin=False, **kwargs):
    base = get_base_url()
    if not base:
        frappe.throw(f"WuzAPI base_url is not set in {SETTINGS}")

    headers = kwargs.pop("headers", {})
    if admin:
        headers["Authorization"] = get_admin_token() or ""
    elif token:
        headers["Token"] = token

    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    resp = requests.request(method, f"{base}{path}", headers=headers, **kwargs)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        return {"raw": resp.text}


# ---------------------------------------------------------------------------
# Admin / session
# ---------------------------------------------------------------------------

def create_user(name, token, webhook=None, events=DEFAULT_EVENTS):
    payload = {"name": name, "token": token, "events": events}
    if webhook:
        payload["webhook"] = webhook
    return _request("POST", "/admin/users", admin=True, json=payload)


def session_connect(token, subscribe=None, immediate=True):
    payload = {"Subscribe": subscribe or ["Message"], "Immediate": immediate}
    return _request("POST", "/session/connect", token=token, json=payload)


def session_qr(token):
    return _request("GET", "/session/qr", token=token)


def session_status(token):
    return _request("GET", "/session/status", token=token)


def session_logout(token):
    return _request("POST", "/session/logout", token=token)


def set_webhook(token, webhook_url, events=DEFAULT_EVENTS):
    return _request(
        "POST", "/webhook", token=token,
        json={"webhookurl": webhook_url, "events": events},
    )


# ---------------------------------------------------------------------------
# Messaging
# ---------------------------------------------------------------------------

def send_text(token, phone, body, link_preview=True):
    return _request(
        "POST", "/chat/send/text", token=token,
        json={"Phone": phone, "Body": body, "LinkPreview": link_preview},
    )


def send_image(token, phone, image_b64, caption=""):
    return _request(
        "POST", "/chat/send/image", token=token,
        json={"Phone": phone, "Image": image_b64, "Caption": caption or ""},
    )


def send_audio(token, phone, audio_b64):
    return _request(
        "POST", "/chat/send/audio", token=token,
        json={"Phone": phone, "Audio": audio_b64},
    )


def send_document(token, phone, document_b64, filename):
    return _request(
        "POST", "/chat/send/document", token=token,
        json={"Phone": phone, "Document": document_b64, "FileName": filename},
    )


def send_contact(token, phone, name, vcard):
    return _request(
        "POST", "/chat/send/contact", token=token,
        json={"Phone": phone, "Name": name, "Vcard": vcard},
    )


# ---------------------------------------------------------------------------
# Users / groups
# ---------------------------------------------------------------------------

def check_users(token, phones):
    return _request("POST", "/user/check", token=token, json={"Phone": phones})


def get_contacts(token):
    return _request("GET", "/user/contacts", token=token)


def get_groups(token):
    return _request("GET", "/group/list", token=token)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def frappe_status_from_session(status_data):
    """Map a /session/status response to the WhatsApp Instance ``status`` select.

    WuzAPI's ``/session/status`` returns lowercase keys:
    ``{"data": {"connected": bool, "loggedIn": bool}}``. We also accept the
    capitalized variants in case a WuzAPI version differs.
    """
    data = (status_data or {}).get("data", status_data or {})
    logged_in = data.get("loggedIn", data.get("LoggedIn"))
    connected = data.get("connected", data.get("Connected"))
    if logged_in:
        return "Open"
    if connected:
        return "Connecting"
    return "Closed"


def phone_from_jid(jid):
    """Extract the bare phone number from a WhatsApp JID.

    e.g. ``220123456:12@s.whatsapp.net`` -> ``220123456``.
    """
    return (jid or "").split("@")[0].split(":")[0]
