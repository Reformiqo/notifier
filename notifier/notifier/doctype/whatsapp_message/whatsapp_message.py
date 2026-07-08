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
        # A send failure (e.g. the WuzAPI gateway returning 500) must not abort
        # the transaction that created this message: the record stays with
        # status "Failed" so it can be inspected and re-sent.
        try:
            if self.content_type == "text":
                self.send_text_message()
            else:
                send_media_message(self.name)
            self.db_set("status", "Sent", update_modified=False)
        except Exception as e:
            # Plain traceback (no frame variables): the notification context
            # holds safe_exec wrappers that crash frappe's variable printer.
            frappe.log_error(
                message=frappe.get_traceback(),
                title="WhatsApp Message Error",
                reference_doctype=self.doctype,
                reference_name=self.name,
            )
            self.db_set("status", "Failed", update_modified=False)
            frappe.msgprint(
                f"Failed to send WhatsApp message: {e}", indicator="red", alert=True
            )

    def send_text_message(self):
        token = wuzapi.instance_token(self.instance)
        if not token:
            frappe.throw(f"No WuzAPI token stored for instance {self.instance}")

        response = wuzapi.send_text(token, self.to, self.message)

        message_id = (response.get("data") or {}).get("Id")
        if message_id:
            self.db_set("message_id", message_id)

        return response
