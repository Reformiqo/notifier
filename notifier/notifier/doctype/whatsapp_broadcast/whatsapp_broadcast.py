# Copyright (c) 2025, royalsmb and contributors
# For license information, please see license.txt

import frappe
import re
from frappe.model.document import Document


class WhatsAppBroadcast(Document):

    def on_submit(self):
        try:
            frappe.enqueue(
                "notifier.notifier.doctype.whatsapp_broadcast.whatsapp_broadcast.send_broadcast",
                broadcast_id=self.name,
            )
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Broadcast Error")
            frappe.throw(str(e))


def replace_template_variables(message, contact_doc):
    """
    Replace {{fieldname}} variables in message with actual values from contact document.

    Args:
            message: The template message string with {{variables}}
            contact_doc: The Contact document object

    Returns:
            Message string with variables replaced
    """
    if not message:
        return message

    # Find all {{variable}} patterns
    pattern = r"\{\{(\w+)\}\}"

    def replace_var(match):
        fieldname = match.group(1)
        # Get value from contact document
        value = getattr(contact_doc, fieldname, None)

        # Handle None values
        if value is None:
            return ""

        # Convert to string and handle HTML content
        return str(value)

    # Replace all variables
    replaced_message = re.sub(pattern, replace_var, message)

    return replaced_message


@frappe.whitelist()
def send_broadcast(broadcast_id):
    try:
        broadcast = frappe.get_doc("WhatsApp Broadcast", broadcast_id)
        if not broadcast.group:
            frappe.throw("Please select a group for the broadcast")

        if not broadcast.template:
            frappe.throw("Please select a template for the broadcast")
        contacts = frappe.db.get_list("Contact", ["name"])
        for contact in contacts:
            contact_doc = frappe.get_doc("Contact", contact.name)
            # Check if groups exists and is not None
            if hasattr(contact_doc, "groups") and contact_doc.groups:
                for group in contact_doc.groups:
                    if group.group == broadcast.group:
                        message = frappe.new_doc("WhatsApp Message")
                        message.label = broadcast.broadcast_name
                        message.instance = broadcast.instance
                        message.to = contact_doc.custom_primary_contact
                        message.type = "Broadcast"
                        message.broadcast_id = broadcast.name
                        template = frappe.get_doc(
                            "WhatsApp Template", broadcast.template
                        )
                        # Replace template variables with contact field values
                        message.message = replace_template_variables(
                            template.message, contact_doc
                        )
                        if template.content_type == "text":
                            message.content_type = "text"
                        elif template.content_type == "image":
                            message.content_type = "image"
                        elif template.content_type == "video":
                            message.content_type = "video"
                        elif template.content_type == "audio":
                            message.content_type = "audio"
                        elif template.content_type == "document":
                            message.content_type = "document"

                        attach = frappe.utils.get_url(template.attach)
                        message.attach = attach
                        message.save()
                        frappe.db.commit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "WhatsApp Broadcast Error")
        frappe.throw(str(e))
