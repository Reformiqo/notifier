"""Public WhatsApp API for the Notifier app, backed by WuzAPI (whatsmeow).

This replaces the old Evolution API backend. The low-level HTTP client lives
in ``notifier/wuzapi.py``; see the README for how to run and configure WuzAPI.
"""

import base64

import frappe
import requests
from frappe.utils.file_manager import save_file

from notifier import wuzapi


def _instance_token_or_throw(instance):
    token = wuzapi.instance_token(instance)
    if not token:
        frappe.throw(f"No WuzAPI token stored for instance {instance}")
    return token


# ---------------------------------------------------------------------------
# Instance lifecycle
# ---------------------------------------------------------------------------

@frappe.whitelist()
def create_instance(instance, phone_number=None, token=None):
    """Register ``instance`` as a WuzAPI user and open its session.

    Called from ``WhatsAppInstance.after_insert``. ``token`` is the per-session
    WuzAPI token stored on the WhatsApp Instance.
    """
    token = token or wuzapi.instance_token(instance)
    if not token:
        frappe.throw(f"No token available for instance {instance}")

    webhook = wuzapi.webhook_url_for(instance)
    try:
        result = wuzapi.create_user(name=instance, token=token, webhook=webhook)
    except requests.HTTPError as e:
        # A non-2xx here usually means the WuzAPI user already exists - not fatal.
        frappe.log_error(
            f"WuzAPI create_user for {instance}: {e.response.text}",
            "WuzAPI create_instance",
        )
        result = {"note": "user may already exist", "error": e.response.text}

    # Kick off the session so a QR code can be fetched from the instance form.
    try:
        wuzapi.session_connect(token, immediate=True)
    except Exception:
        frappe.logger().info("session/connect no-op for %s", instance)

    return result


@frappe.whitelist()
def reconcile_instance_status(instance):
    """Query WuzAPI for the live session state and store it on the instance."""
    token = wuzapi.instance_token(instance)
    if not token:
        return None

    status = wuzapi.session_status(token)
    fstatus = wuzapi.frappe_status_from_session(status)

    updates = {"status": fstatus}
    if fstatus == "Open":
        updates["qr_code"] = None
    frappe.db.set_value("WhatsApp Instance", instance, updates)
    frappe.db.commit()
    return fstatus


@frappe.whitelist()
def connection_status(instance_name):
    """Back-compat: return ``{"state": open|connecting|close, "data": ...}``."""
    token = wuzapi.instance_token(instance_name)
    if not token:
        return {"state": "unknown"}
    try:
        status = wuzapi.session_status(token)
    except Exception as e:
        return {"state": "unknown", "error": str(e)}

    state = {"Open": "open", "Connecting": "connecting", "Closed": "close"}[
        wuzapi.frappe_status_from_session(status)
    ]
    return {"state": state, "data": status.get("data", status)}


@frappe.whitelist()
def check_instance_status():
    """Reconcile status for every WhatsApp Instance."""
    out = {}
    for name in frappe.get_all("WhatsApp Instance", pluck="name"):
        try:
            out[name] = reconcile_instance_status(name)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "WuzAPI check_instance_status")
    return out


@frappe.whitelist()
def get_instance(instance_name, phone_number=None):
    """Open the session and return connect + QR info for ``instance_name``."""
    token = _instance_token_or_throw(instance_name)
    connect = wuzapi.session_connect(token, immediate=True)
    qr = wuzapi.session_qr(token)
    qr_data = qr.get("data") or {}
    return {
        "connect": connect,
        "qr": qr_data.get("QRCode") or qr_data.get("qrcode"),
        "status": wuzapi.session_status(token),
    }


@frappe.whitelist()
def get_instance_token(instance):
    return frappe.db.get_value("WhatsApp Instance", instance, "token")


# ---------------------------------------------------------------------------
# Messaging
# ---------------------------------------------------------------------------

@frappe.whitelist()
def send_text_message(instance, phone, message):
    return wuzapi.send_text(_instance_token_or_throw(instance), phone, message)


@frappe.whitelist()
def send_media_message(docname):
    """Send the attachment on a WhatsApp Message via WuzAPI.

    WuzAPI does not fetch remote URLs, so the file is read and base64-encoded.
    """
    doc = frappe.get_doc("WhatsApp Message", docname)
    token = _instance_token_or_throw(doc.instance)
    phone = doc.to
    caption = doc.message or ""

    b64 = get_attachment_as_base64(docname)
    filename = (doc.attach or "file").split("/")[-1]
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ctype = (doc.content_type or "").lower()

    if ctype in ("image", "photo") or ext in ("jpg", "jpeg", "png", "gif", "webp"):
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext or 'png'}"
        resp = wuzapi.send_image(token, phone, f"data:{mime};base64,{b64}", caption)
    elif ctype == "audio" or ext in ("ogg", "opus", "mp3", "m4a"):
        # WuzAPI expects Opus/OGG audio; other formats may be rejected by WhatsApp.
        resp = wuzapi.send_audio(token, phone, f"data:audio/ogg;base64,{b64}")
    else:
        resp = wuzapi.send_document(
            token, phone, f"data:application/octet-stream;base64,{b64}", filename
        )

    msg_id = (resp.get("data") or {}).get("Id")
    if msg_id:
        frappe.db.set_value("WhatsApp Message", docname, "message_id", msg_id)
        frappe.db.commit()
    return resp


@frappe.whitelist()
def send_audio_message(instance, phone, audio_b64):
    """Send audio. ``audio_b64`` must be base64 (Opus/OGG); WuzAPI won't fetch URLs."""
    if not audio_b64.startswith("data:"):
        audio_b64 = f"data:audio/ogg;base64,{audio_b64}"
    return wuzapi.send_audio(_instance_token_or_throw(instance), phone, audio_b64)


@frappe.whitelist()
def send_contact_message(instance, phone, name, vcard):
    return wuzapi.send_contact(_instance_token_or_throw(instance), phone, name, vcard)


# ---------------------------------------------------------------------------
# Groups / contacts
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_groups(instance):
    return wuzapi.get_groups(_instance_token_or_throw(instance))


@frappe.whitelist()
def get_contact_list(instance):
    """Pull the WhatsApp contact list and mirror new ones into WhatsApp Contact."""
    token = _instance_token_or_throw(instance)
    data = wuzapi.get_contacts(token)
    contacts = data.get("data") or {} if isinstance(data, dict) else {}

    for jid, info in contacts.items():
        if not isinstance(info, dict) or not info.get("Found"):
            continue
        if frappe.db.exists("WhatsApp Contact", {"phone_number": jid}):
            continue
        doc = frappe.new_doc("WhatsApp Contact")
        doc.full_name = (
            info.get("FullName") or info.get("PushName") or info.get("FirstName")
        )
        doc.phone_number = jid
        doc.instance = instance
        doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return contacts


# ---------------------------------------------------------------------------
# Generic file helpers (provider-agnostic; used by instance/message controllers)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_attachment_as_base64(docname, doctype="WhatsApp Message"):
    """Return the document's attachment as a raw base64 string."""
    try:
        doc = frappe.get_doc(doctype, docname)
        if not getattr(doc, "attach", None):
            frappe.throw("No attachment found in the document")

        file_path = doc.attach
        file_doc = None
        file_docs = frappe.get_all(
            "File",
            filters={"attached_to_doctype": doctype, "attached_to_name": docname},
            fields=["name"],
            order_by="creation desc",
            limit=1,
        )
        if file_docs:
            file_doc = frappe.get_doc("File", file_docs[0].name)

        if not file_doc:
            search_path = file_path if file_path.startswith("/") else f"/{file_path}"
            file_docs = frappe.get_all(
                "File", filters={"file_url": search_path}, fields=["name"], limit=1
            )
            if file_docs:
                file_doc = frappe.get_doc("File", file_docs[0].name)

        if not file_doc:
            frappe.throw(f"File not found for attachment: {doc.attach}")

        file_content = file_doc.get_content()
        if isinstance(file_content, str):
            file_content = file_content.encode("utf-8")

        return base64.b64encode(file_content).decode("utf-8")

    except Exception as e:
        frappe.log_error(
            f"Error converting attachment to base64: {str(e)}",
            "Attachment to Base64 Error",
        )
        frappe.throw(f"Failed to convert attachment to base64: {str(e)}")


def save_base64_image_as_file(
    base64_string, filename, doctype=None, docname=None, folder=None, is_private=0
):
    """Decode a base64 (optionally data-URI) image and store it as a File."""
    try:
        if base64_string.startswith("data:"):
            base64_string = base64_string.split(",")[1]
        base64_string = base64_string.strip().replace("\n", "").replace("\r", "")

        file_content = base64.b64decode(base64_string)
        if len(file_content) == 0:
            raise ValueError("Decoded file content is empty")

        file_doc = save_file(
            fname=filename,
            content=file_content,
            dt=doctype,
            dn=docname,
            folder=folder,
            is_private=is_private,
        )
        frappe.db.commit()
        return file_doc

    except base64.binascii.Error as e:
        frappe.log_error(f"Base64 decode error: {str(e)}", "Base64 Decode Error")
        frappe.throw(f"Invalid base64 data: {str(e)}")
    except Exception as e:
        frappe.log_error(
            f"Error saving base64 image: {str(e)}", "Base64 Image Save Error"
        )
        frappe.throw(f"Failed to save image: {str(e)}")
