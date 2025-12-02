# Copyright (c) 2025, royalsmb and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document

base_url = frappe.db.get_single_value("Evolution API Settings", "base_url")
api_token = frappe.db.get_single_value("Evolution API Settings", "api_token")


class WhatsAppMessage(Document):
    def validate(self):
        if self.to.startswith("+"):
            self.to = self.to[1:]
        self.send_message()

    def send_message(self):
        if self.content_type == "text":
            self.send_text_message()
       
    def send_text_message(self):

        try:
            url = f"{base_url}/message/sendText/{self.instance}"

            payload = {
                "number": self.to,
                "text": self.message,
                "linkPreview": True,
            }
            headers = {"apikey": api_token, "Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes

            response_data = response.json()
            key_data = response_data.get("key")
            if key_data:
                self.message_id = key_data.get("id")

            return response_data
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Message Error")
            frappe.throw(f"Failed to send WhatsApp message: {str(e)}")

    def send_media_message(self):
        try:
            if not self.attach:
                frappe.throw("Please attach a file to send media message")

            extension = self.attach.split(".")[-1].lower()
            mimetype = self.content_type + "/" + extension

            # Get full URL for the attached file
            # Ensure path starts with / if it doesn't already
            file_path = (
                self.attach if self.attach.startswith("/") else f"/{self.attach}"
            )
            media_url = frappe.utils.get_url(file_path)

            url = f"{base_url}/message/sendMedia/{self.instance}"

            payload = {
                "number": self.to,
                "mediatype": self.content_type,
                "mimetype": mimetype,
                "caption": self.message,
                "media": media_url,
                "fileName": self.label,
                "linkPreview": True,
            }
            headers = {"apikey": api_token, "Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes

            response_data = response.json()
            frappe.log_error(response_data, "WhatsApp Message Error")
            key_data = response_data.get("key")
            if key_data:
                self.message_id = key_data.get("id")

            return response_data
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Message Error")
            frappe.throw(f"Failed to send WhatsApp media message: {str(e)}")
