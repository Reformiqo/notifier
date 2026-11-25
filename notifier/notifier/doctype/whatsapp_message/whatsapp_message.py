# Copyright (c) 2025, royalsmb and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document

from notifier import wuzapi
from notifier.api import send_media_message


def normalize_phone(phone):
    """Digits only, no trunk zero, and the default country code on bare
    10-digit local numbers (WhatsApp needs the full international number)."""
    phone = re.sub(r"^0+", "", re.sub(r"\D", "", phone or ""))
    if len(phone) == 10:
        code = frappe.db.get_single_value("WhatsApp Settings", "default_country_code")
        # None = setting never saved; fall back to the field default.
        code = re.sub(r"\D", "", "91" if code is None else code)
        phone = f"{code}{phone}"
    return phone


class WhatsAppMessage(Document):
    def validate(self):
        # When sending to a group, the target is the group's JID.
        if self.get("send_to") == "Group" and self.get("group"):
            self.to = frappe.db.get_value("WhatsApp Group", self.group, "group_id")
        # WuzAPI wants digits only: drop +, spaces, dashes and any trunk zero.
        if self.to and "@" not in self.to:
            self.to = normalize_phone(self.to)

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
            frappe.throw(f"WhatsApp send to {self.to} via {self.instance} failed: {e}")
