"""Manual "Send WhatsApp" from any document form.

The button (``public/js/send_whatsapp.js``) is shown on doctypes that have an
enabled Notification with channel "WhatsApp". Clicking it sends the document
straight through that Notification's WhatsApp Instance (WuzAPI) - message body,
recipient and print-format PDF all come from the Notification - instead of
opening WhatsApp Web in the browser.
"""

import frappe
from frappe import _
from frappe.email.doctype.notification.notification import get_context


def _whatsapp_notifications(doctype):
	return frappe.get_all(
		"Notification",
		filters={"document_type": doctype, "channel": "WhatsApp", "enabled": 1},
		fields=["name", "whatsapp_send_to", "whatsapp_group", "attach_print", "print_format"],
		order_by="name asc",
	)


def boot_session(bootinfo):
	"""Tell the desk which doctypes get the Send WhatsApp button."""
	try:
		bootinfo.notifier_whatsapp_doctypes = sorted(
			set(
				frappe.get_all(
					"Notification",
					filters={"channel": "WhatsApp", "enabled": 1},
					pluck="document_type",
				)
			)
		)
	except Exception:
		# e.g. custom fields not migrated yet - never break login.
		bootinfo.notifier_whatsapp_doctypes = []


@frappe.whitelist()
def get_send_options(doctype, name):
	"""Notifications usable for this document, with their default recipients."""
	frappe.has_permission(doctype, "read", name, throw=True)
	doc = frappe.get_doc(doctype, name)

	out = []
	for row in _whatsapp_notifications(doctype):
		notification = frappe.get_doc("Notification", row.name)
		is_group = notification.get("whatsapp_send_to") == "Group"
		out.append(
			{
				"name": row.name,
				"send_to": "Group" if is_group else "Phone",
				"group": notification.get("whatsapp_group"),
				"phone": "" if is_group else ", ".join(notification.get_whatsapp_numbers(doc)),
				"attach_print": row.attach_print,
				"print_format": row.print_format,
			}
		)
	return out


@frappe.whitelist()
def send_document(doctype, name, notification, phone=None):
	"""Send ``doctype``/``name`` now via the WhatsApp Notification's instance."""
	frappe.has_permission(doctype, "read", name, throw=True)

	notif = frappe.get_doc("Notification", notification)
	if notif.channel != "WhatsApp" or notif.document_type != doctype:
		frappe.throw(_("{0} is not a WhatsApp Notification for {1}").format(notification, doctype))

	doc = frappe.get_doc(doctype, name)
	if notif.attach_print:
		frappe.has_permission(doctype, "print", name, throw=True)

	targets = None
	if notif.get("whatsapp_send_to") != "Group" and phone:
		targets = [p.strip() for p in phone.replace(";", ",").split(",") if p.strip()]

	targets = targets or notif.get_recipients(doc)
	if not targets:
		frappe.throw(_("No WhatsApp recipient found. Enter a phone number."))

	# Errors from WuzAPI propagate so the user sees why a send failed.
	sent = notif.send_whatsapp(doc, get_context(doc), targets=targets)
	if not sent:
		frappe.throw(_("Nothing to send: the Notification has no message and no PDF attachment."))

	doc.add_comment(
		"Info", _("Sent on WhatsApp to {0} via {1}").format(", ".join(targets), notif.whatsapp_instance)
	)
	return {"targets": targets, "messages": sent}
