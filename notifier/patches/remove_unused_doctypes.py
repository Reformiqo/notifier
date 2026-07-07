"""Drop unused/broken doctypes left over from the pre-WuzAPI app.

These had no controller logic and nothing populated them (the Bulk-messaging
cluster was a non-functional stub that even linked a non-existent doctype).
Runs post_model_sync. As a safety net, a doctype is only dropped if its table is
empty; if it somehow holds rows, it is skipped and logged so nothing is lost.
"""

import frappe

UNUSED = [
    "WhatsApp QR",
    "WhatsApp Instance Update",
    "WhatsApp Message Fields",
    "Bulk WhatsApp Message",
    "WhatsApp Recipient",
    "WhatsApp Recipient List",
    "WhatsApp Notification Log",
]


def execute():
    for dt in UNUSED:
        if not frappe.db.exists("DocType", dt):
            continue
        try:
            rows = frappe.db.count(dt)
        except Exception:
            rows = 0
        if rows:
            frappe.log_error(
                f"Not deleting DocType {dt}: it has {rows} row(s).",
                "notifier: remove_unused_doctypes",
            )
            continue
        frappe.delete_doc("DocType", dt, force=True, ignore_permissions=True)
