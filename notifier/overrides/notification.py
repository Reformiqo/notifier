"""Adds a "WhatsApp" channel to Frappe's standard Notification doctype.

Frappe's ``Notification.send_notification_by_channel`` dispatches on ``channel``
with a hardcoded if/elif and no plugin hook, so we subclass it via
``override_doctype_class`` (see hooks.py) and handle the WhatsApp channel here,
delegating every other channel to the core implementation.

A WhatsApp Notification reuses the native Notification config plus custom fields:
  * ``message``            -> the WhatsApp text body (Jinja + HTML, stripped)
  * ``whatsapp_instance``  -> which WhatsApp Instance to send from
  * ``whatsapp_send_to``   -> "Phone" or "Group"
      - Phone: ``whatsapp_recipient_field`` and/or Recipients rows hold the number
      - Group: ``whatsapp_group`` selects a WhatsApp Group (sent to its JID)
  * ``attach_print`` / ``print_format`` -> also send the document's PDF

Sending goes through the WhatsApp Message doctype, so every alert is logged and
uses the same WuzAPI pipeline as manual messages.
"""

import frappe
from frappe import _
from frappe.email.doctype.notification.notification import Notification
from frappe.utils import strip_html_tags


class WhatsAppNotification(Notification):
	def validate(self):
		super().validate()
		if self.channel != "WhatsApp":
			return
		if not self.get("whatsapp_instance"):
			frappe.throw(_("Please select a WhatsApp Instance for the WhatsApp channel."))
		if self.get("whatsapp_send_to") == "Group":
			if not self.get("whatsapp_group"):
				frappe.throw(_("Please select a WhatsApp Group to send to."))
		elif not self.get("whatsapp_recipient_field") and not self.recipients:
			frappe.throw(
				_("Set a recipient phone field (or a Recipients row) for the WhatsApp channel.")
			)

	def send_notification_by_channel(self, doc, context):
		if self.channel != "WhatsApp":
			return super().send_notification_by_channel(doc, context)

		try:
			self.send_whatsapp(doc, context)
		except Exception:
			# frappe.get_traceback() without with_context: the Jinja `context`
			# in these frames holds safe_exec module wrappers that fail
			# deepcopy inside frappe's traceback variable printer.
			frappe.log_error(
				message=frappe.get_traceback(),
				title=f"Failed to send WhatsApp Notification: {self.name}",
				reference_doctype=self.doctype,
				reference_name=self.name,
			)

		if self.send_system_notification:
			self.create_system_notification(doc, context)

	# --- WhatsApp channel ---------------------------------------------------

	def get_recipients(self, doc):
		"""Resolve the send targets: a group JID, or phone number(s)."""
		if self.get("whatsapp_send_to") == "Group":
			group = self.get("whatsapp_group")
			jid = frappe.db.get_value("WhatsApp Group", group, "group_id") if group else None
			return [jid] if jid else []
		return self.get_whatsapp_numbers(doc)

	def get_whatsapp_numbers(self, doc):
		"""Collect recipient phone numbers from the field and/or Recipients table."""
		numbers = []
		if self.get("whatsapp_recipient_field"):
			numbers.append(doc.get(self.whatsapp_recipient_field))
		for row in self.recipients or []:
			if row.receiver_by_document_field:
				numbers.append(doc.get(row.receiver_by_document_field))

		seen, out = set(), []
		for n in numbers:
			n = str(n).strip() if n else ""
			if n and n not in seen:
				seen.add(n)
				out.append(n)
		return out

	def send_whatsapp(self, doc, context):
		targets = self.get_recipients(doc)
		if not targets:
			return

		body = self.message or ""
		if "{" in body:
			body = frappe.render_template(body, context)
		body = strip_html_tags(body).strip()

		pdf_file_url = self.build_pdf_file(doc) if self.attach_print else None

		for target in targets:
			if body:
				self.queue_whatsapp_message(target, "text", message=body)
			if pdf_file_url:
				self.queue_whatsapp_message(target, "document", message="", attach=pdf_file_url)

	def build_pdf_file(self, doc):
		"""Render the document's print format to a PDF File and return its url."""
		pdf = frappe.get_print(
			doc.doctype, doc.name, print_format=self.print_format or None, as_pdf=True
		)
		fname = f"{doc.doctype}-{doc.name}.pdf".replace("/", "-").replace(" ", "-")
		file_doc = frappe.get_doc(
			{"doctype": "File", "file_name": fname, "content": pdf, "is_private": 1}
		).insert(ignore_permissions=True)
		return file_doc.file_url

	def queue_whatsapp_message(self, to, content_type, message="", attach=None):
		msg = frappe.new_doc("WhatsApp Message")
		msg.label = self.name
		msg.instance = self.whatsapp_instance
		msg.to = to
		msg.type = "Single"
		msg.content_type = content_type
		msg.message = message
		if attach:
			msg.attach = attach
		# WhatsAppMessage.after_insert dispatches the send via WuzAPI.
		msg.insert(ignore_permissions=True)
