# Copyright (c) 2025, royalsmb and contributors
# For license information, please see license.txt

import uuid
from datetime import datetime

import frappe
from frappe.model.document import Document

from notifier import wuzapi
from notifier.api import (
    create_instance,
    reconcile_instance_status,
    save_base64_image_as_file,
)


class WhatsAppInstance(Document):
    def validate(self):
        if not self.token:
            self.token = str(uuid.uuid4())

    def after_insert(self):
        phone_number = getattr(self, "phone_number", None) or self.name
        create_instance(self.name, phone_number, self.token)


@frappe.whitelist()
def connect_instance(instance):
    """Open the WuzAPI session for ``instance`` and store its QR code.

    Invoked by the "Refresh QR Code" button in whatsapp_instance.js.
    Returns ``{"success", "file_url", "message"}`` for back-compat with the JS.
    """
    token = wuzapi.instance_token(instance)
    if not token:
        frappe.throw(f"No WuzAPI token stored for instance {instance}")

    # Ensure the session is up. Re-connecting an active session may error; ignore.
    try:
        wuzapi.session_connect(token, immediate=True)
    except Exception:
        frappe.logger().info("session/connect no-op for %s", instance)

    qr = wuzapi.session_qr(token)
    qr_data = qr.get("data") or {}
    qr_code = qr_data.get("QRCode") or qr_data.get("qrcode")

    if not qr_code:
        # No QR usually means the instance is already logged in.
        if wuzapi.frappe_status_from_session(wuzapi.session_status(token)) == "Open":
            frappe.db.set_value(
                "WhatsApp Instance", instance, {"status": "Open", "qr_code": None}
            )
            frappe.db.commit()
            return {
                "success": True,
                "file_url": None,
                "message": "Instance already connected",
            }
        frappe.throw(f"No QR code returned by WuzAPI for {instance}: {qr}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"qrcode_{instance}_{timestamp}.png"
    file_doc = save_base64_image_as_file(
        qr_code, filename, doctype="WhatsApp Instance", docname=instance
    )
    frappe.db.set_value("WhatsApp Instance", instance, "qr_code", file_doc.file_url)
    frappe.db.commit()

    return {
        "success": True,
        "file_url": file_doc.file_url,
        "message": "QR code generated successfully",
    }


@frappe.whitelist()
def get_instance(instance_name=None):
    """Back-compat alias: connect and return the QR code."""
    if not instance_name:
        frappe.throw("Instance name is required")
    return connect_instance(instance_name)


@frappe.whitelist()
def refresh_qr_code(instance_name=None):
    """Log the session out and fetch a fresh QR code."""
    if not instance_name:
        frappe.throw("Instance name is required")

    token = wuzapi.instance_token(instance_name)
    if token:
        try:
            wuzapi.session_logout(token)
        except Exception:
            pass  # Ignore if there was nothing to log out of.

    return connect_instance(instance_name)


@frappe.whitelist()
def get_instance_status(instance):
    """Reconcile and return the live session status for ``instance``."""
    reconcile_instance_status(instance)
    token = wuzapi.instance_token(instance)
    return wuzapi.session_status(token) if token else {"state": "unknown"}


@frappe.whitelist()
def check_instance_status(instance_name=None):
    if not instance_name:
        frappe.throw("Instance name is required")
    token = wuzapi.instance_token(instance_name)
    return wuzapi.session_status(token) if token else {"state": "unknown"}


@frappe.whitelist()
def sync_groups(instance):
    """Fetch this instance's WhatsApp groups from WuzAPI into WhatsApp Group."""
    token = wuzapi.instance_token(instance)
    if not token:
        return {"fetched": 0, "new": 0}

    data = wuzapi.get_groups(token)
    groups = (data.get("data") or {}).get("Groups") or [] if isinstance(data, dict) else []

    new = 0
    for g in groups:
        jid = g.get("JID")
        if not jid:
            continue
        values = {
            "group_name": g.get("Name") or jid,
            "participant_count": len(g.get("Participants") or []),
        }
        existing = frappe.db.get_value(
            "WhatsApp Group", {"group_id": jid, "instance": instance}, "name"
        )
        if existing:
            frappe.db.set_value("WhatsApp Group", existing, values)
        else:
            doc = frappe.new_doc("WhatsApp Group")
            doc.group_id = jid
            doc.instance = instance
            doc.update(values)
            doc.insert(ignore_permissions=True)
            new += 1

    frappe.db.commit()
    return {"fetched": len(groups), "new": new}


@frappe.whitelist()
def check_connection(instance):
    """Reconcile status and, if connected, sync the instance's WhatsApp groups.

    Invoked by the "Check Connection" button.
    """
    status = reconcile_instance_status(instance)
    result = {"status": status}
    if status == "Open":
        try:
            result["groups"] = sync_groups(instance)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "WuzAPI sync_groups")
    return result
