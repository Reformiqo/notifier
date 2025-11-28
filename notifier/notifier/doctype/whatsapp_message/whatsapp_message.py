# Copyright (c) 2025, royalsmb and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from frappe.model.document import Document
base_url = frappe.db.get_single_value("Evolution API Settings", "base_url")
api_token = frappe.db.get_single_value("Evolution API Settings", "api_token")

class WhatsAppMessage(Document):
    def validate(self):
        if self.to.startswith("+"):
            self.to = self.to[1:]
        self.send_message()
    
        
    
    def send_text_message(self):

        try:
            url = f"{base_url}/message/sendText/{self.instance}"

            payload = {
                "number": self.to,
                "text": self.message,
                "linkPreview": True,
            }
            headers = {
                "apikey": api_token,
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers)
            self.message_id = response.json().get("key").get("id")

            return response.json()
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Message Error")
            frappe.throw(f"Failed to send WhatsApp message: {str(e)}")

    
    def send_media_message(self):
        try:
            extension = self.attach.split(".")[-1]
            mimetype = self.content_type + "/" + extension

                

            url = f"{base_url}/message/sendMedia/{self.instance}"
            

            payload = {
                "number": self.to,
                "mediatype": self.content_type,
                "mimetype": mimetype,
                "caption": self.message,
                "media": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                "fileName": self.label,
                "linkPreview": True,
                
            }
            headers = {
                "apikey": api_token,
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers)
            self.message_id = response.json().get("key").get("id")

            return response.json()
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Message Error")

   