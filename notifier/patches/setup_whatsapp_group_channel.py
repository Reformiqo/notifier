"""Add the Phone/Group destination fields to the WhatsApp notification channel.

After picking a WhatsApp Instance the user chooses whether the alert goes to a
phone number or a group chat. For groups they pick a WhatsApp Group (populated by
the instance's "Check Connection"). Idempotent.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "Notification": [
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
                        "Fieldname on the document that holds the recipient's phone "
                        "number with country code (e.g. mobile_no). You may also use "
                        "the Recipients table's 'by document field'."
                    ),
                },
            ]
        },
        ignore_validate=True,
    )
