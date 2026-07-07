"""Set up the WhatsApp channel on the standard Notification doctype.

Adds "WhatsApp" to the Notification ``channel`` options and the custom fields
that configure a WhatsApp alert (which instance to send from, which field holds
the recipient's phone number). Idempotent.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    # 1. Add "WhatsApp" to the channel Select options (via a Property Setter).
    channel = frappe.get_meta("Notification").get_field("channel")
    options = [o for o in (channel.options or "").split("\n") if o]
    if "WhatsApp" not in options:
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

    # 2. Custom fields shown only for the WhatsApp channel.
    create_custom_fields(
        {
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
            ]
        },
        ignore_validate=True,
    )
