"""Idempotent setup for the WhatsApp Notification channel.

Run from BOTH ``after_install`` and ``after_migrate`` hooks (see hooks.py) so it
applies on fresh installs *and* upgrades. This matters because Frappe marks an
app's patches as "already run" on a fresh install without executing them, so the
channel option + custom fields must be (re)applied from a hook, not only a patch.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

WHATSAPP_FIELDS = {
    "Notification": [
        {
            "fieldname": "whatsapp_instance",
            "label": "WhatsApp Instance",
            "fieldtype": "Link",
            "options": "WhatsApp Instance",
            "insert_after": "channel",
            "depends_on": "eval:doc.channel=='WhatsApp'",
            "mandatory_depends_on": "eval:doc.channel=='WhatsApp'",
        },
        {
            "fieldname": "whatsapp_send_to",
            "label": "Send To",
            "fieldtype": "Select",
            "options": "Phone\nGroup",
            "default": "Phone",
            "insert_after": "whatsapp_instance",
            "depends_on": "eval:doc.channel=='WhatsApp'",
            "mandatory_depends_on": "eval:doc.channel=='WhatsApp'",
        },
        {
            "fieldname": "whatsapp_group",
            "label": "WhatsApp Group",
            "fieldtype": "Link",
            "options": "WhatsApp Group",
            "insert_after": "whatsapp_send_to",
            "depends_on": "eval:doc.channel=='WhatsApp' && doc.whatsapp_send_to=='Group'",
            "mandatory_depends_on": "eval:doc.channel=='WhatsApp' && doc.whatsapp_send_to=='Group'",
        },
        {
            "fieldname": "whatsapp_recipient_field",
            "label": "Recipient Phone Field",
            "fieldtype": "Data",
            "insert_after": "whatsapp_group",
            "depends_on": "eval:doc.channel=='WhatsApp' && doc.whatsapp_send_to!='Group'",
            "description": (
                "Fieldname on the document that holds the recipient's phone number "
                "with country code (e.g. mobile_no). You may also use the Recipients "
                "table's 'by document field'."
            ),
        },
    ]
}


def setup_notification_channel():
    """Add the WhatsApp channel option + custom fields to Notification."""
    add_whatsapp_channel_option()
    create_custom_fields(WHATSAPP_FIELDS, ignore_validate=True)
    frappe.clear_cache(doctype="Notification")


def add_whatsapp_channel_option():
    channel = frappe.get_meta("Notification").get_field("channel")
    options = [o for o in (channel.options or "").split("\n") if o]
    if "WhatsApp" in options:
        return
    options.append("WhatsApp")
    frappe.make_property_setter(
        {
            "doctype": "Notification",
            "fieldname": "channel",
            "property": "options",
            "value": "\n".join(options),
            "property_type": "Text",
        },
        is_system_generated=True,
    )
