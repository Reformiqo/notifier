# Copyright (c) 2025, royalsmb and contributors
# For license information, please see license.txt

import frappe
import base64
from frappe.model.document import Document
from frappe.utils.file_manager import save_file

class WhatsAppQR(Document):
	def validate(self):
		if self.base64:
			self.save_base64_image_as_file()
			
	
