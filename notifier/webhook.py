"""Inbound webhook endpoint for WuzAPI events.

WuzAPI is configured (at user-create time, see ``wuzapi.webhook_url_for``) to POST
events here with ``?instance=<name>`` so we can tell which WhatsApp Instance an
event belongs to. On any connection-related event we re-query the live session
state and store it on the instance.
"""

import json

import frappe

from notifier.api import reconcile_instance_status

# whatsmeow / WuzAPI event types that imply the connection state may have changed.
CONNECTION_EVENTS = {
    "Connected",
    "Disconnected",
    "LoggedOut",
    "LoggedIn",
    "PairSuccess",
    "StreamReplaced",
}


def _read_payload():
    if frappe.request and getattr(frappe.request, "is_json", False):
        return frappe.request.json or {}

    form = dict(frappe.local.form_dict or {})
    # WuzAPI can post the event JSON inside a ``jsonData`` form field.
    if "jsonData" in form:
        try:
            return json.loads(form["jsonData"])
        except Exception:
            return form
    return form


@frappe.whitelist(allow_guest=True)
def update_instance():
    try:
        instance = frappe.form_dict.get("instance")
        data = _read_payload()
        event_type = data.get("type") or data.get("event")

        frappe.logger().info("WuzAPI webhook (%s): %s", instance, event_type)

        if not instance or not frappe.db.exists("WhatsApp Instance", instance):
            return {"status": "ignored", "message": f"Unknown instance: {instance}"}

        if event_type in CONNECTION_EVENTS:
            frappe.set_user("Administrator")
            new_status = reconcile_instance_status(instance)
            return {"status": "success", "instance": instance, "state": new_status}

        return {"status": "ignored", "event": event_type}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "WuzAPI Webhook Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist(allow_guest=True)
def send_message(doc, method=None):
    pass


@frappe.whitelist(allow_guest=True)
def receive_message():
    pass
