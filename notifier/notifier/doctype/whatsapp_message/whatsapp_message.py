# Copyright (c) 2025, royalsmb and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from notifier import wuzapi
from notifier.api import send_media_message


class WhatsAppMessage(Document):
    def validate(self):
        # When sending to a group, the target is the group's JID.
        if self.get("send_to") == "Group" and self.get("group"):
            self.to = frappe.db.get_value("WhatsApp Group", self.group, "group_id")
        if self.to and self.to.startswith("+"):
            self.to = self.to[1:]

    def after_insert(self):
        if self.content_type == "text":
            self.send_text_message()
        else:
            send_media_message(self.name)

    def send_text_message(self):
        try:
            token = wuzapi.instance_token(self.instance)
            if not token:
                frappe.throw(f"No WuzAPI token stored for instance {self.instance}")

            response = wuzapi.send_text(token, self.to, self.message)

            message_id = (response.get("data") or {}).get("Id")
            if message_id:
                self.db_set("message_id", message_id)

            return response
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Message Error")
            frappe.throw(f"Failed to send WhatsApp message: {str(e)}")
