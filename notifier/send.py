"""Manual "Actions > Send WhatsApp" from list and form views.

Select one or more documents (e.g. Sales Invoices), click Actions > Send
WhatsApp, choose the WhatsApp Instance and Print Format, and each document's
PDF is sent straight to its party's phone number through that instance
(WuzAPI). Nothing opens in the browser. The UI lives in
``public/js/send_whatsapp.js``.
"""

import json

import frappe
from frappe import _

# Above this many documents the send runs as a background job.
SYNC_LIMIT = 5

DEFAULT_MESSAGE = (
	"Dear {{ doc.customer_name or doc.supplier_name or doc.party_name or 'Customer' }},\n"
	"Please find attached {{ doc.doctype }} {{ doc.name }}."
)

# Phone-bearing fields checked on the document itself, in priority order.
DOC_PHONE_FIELDS = ("contact_mobile", "mobile_no", "contact_phone", "phone", "phone_no")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def build_pdf_file(doc, print_format=None, letterhead=None, no_letterhead=0):
	"""Render ``doc`` with ``print_format`` to a private PDF File; return its url."""
	pdf = frappe.get_print(
		doc.doctype,
		doc.name,
		print_format=print_format or None,
		as_pdf=True,
		letterhead=letterhead or None,
		no_letterhead=no_letterhead,
	)
	fname = f"{doc.name}.pdf".replace("/", "-").replace(" ", "-")
	file_doc = frappe.get_doc(
		{"doctype": "File", "file_name": fname, "content": pdf, "is_private": 1}
	).insert(ignore_permissions=True)
	return file_doc.file_url


def get_party_phone(doc):
	"""Best-effort phone number of the document's customer / supplier / party."""
	# 1. Phone fields on the document (standard first, then custom *phone*/*mobile*).
	for f in DOC_PHONE_FIELDS:
		if doc.get(f):
			return str(doc.get(f))
	for df in doc.meta.fields:
		name = df.fieldname or ""
		if (
			df.fieldtype in ("Data", "Phone")
			and ("mobile" in name or "phone" in name)
			and "company" not in name
		):
			if doc.get(name):
				return str(doc.get(name))

	# 2. The linked contact person.
	if doc.get("contact_person"):
		mobile, phone = frappe.db.get_value(
			"Contact", doc.contact_person, ["mobile_no", "phone"]
		) or (None, None)
		if mobile or phone:
			return mobile or phone

	# 3. The party record, then its primary/any linked contact.
	party_type, party = None, None
	for dt in ("customer", "supplier"):
		if doc.get(dt):
			party_type, party = dt.title(), doc.get(dt)
			break
	if not party and doc.get("party_type") and doc.get("party"):
		party_type, party = doc.party_type, doc.party
	if not party and doc.get("quotation_to") and doc.get("party_name"):
		party_type, party = doc.quotation_to, doc.party_name
	if not party:
		return None

	if frappe.get_meta(party_type).has_field("mobile_no"):
		mobile = frappe.db.get_value(party_type, party, "mobile_no")
		if mobile:
			return mobile

	contacts = frappe.get_all(
		"Contact",
		filters=[
			["Dynamic Link", "link_doctype", "=", party_type],
			["Dynamic Link", "link_name", "=", party],
		],
		fields=["mobile_no", "phone"],
		order_by="is_primary_contact desc, modified desc",
	)
	for c in contacts:
		if c.mobile_no or c.phone:
			return c.mobile_no or c.phone
	return None


def _queue_message(instance, to, content_type, message="", attach=None, label=None):
	msg = frappe.new_doc("WhatsApp Message")
	msg.label = label
	msg.instance = instance
	msg.to = to
	msg.type = "Single"
	msg.content_type = content_type
	msg.message = message
	if attach:
		msg.attach = attach
	# WhatsAppMessage.after_insert sends it via WuzAPI (raises on failure).
	msg.insert(ignore_permissions=True)
	return msg.name


# ---------------------------------------------------------------------------
# Whitelisted API used by the dialog
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_dialog_defaults(doctype, names):
	"""Defaults for the dialog: instance, print format, message, phone(s)."""
	names = frappe.parse_json(names) if isinstance(names, str) else names
	instances = frappe.get_all(
		"WhatsApp Instance", filters={"status": "Open"}, pluck="name", order_by="modified desc"
	)
	phones = {}
	for name in names[:50]:
		if frappe.has_permission(doctype, "read", name):
			phones[name] = get_party_phone(frappe.get_doc(doctype, name)) or ""
	return {
		"instance": instances[0] if len(instances) == 1 else None,
		"print_format": frappe.get_meta(doctype).default_print_format or "Standard",
		"message": DEFAULT_MESSAGE,
		"phones": phones,
	}


@frappe.whitelist()
def send_documents(doctype, names, instance, print_format=None, message=None, phone=None,
		no_letterhead=0):
	"""Send each document's PDF to its party's number via ``instance``.

	``phone`` overrides the number (only used when a single document is sent).
	"""
	names = frappe.parse_json(names) if isinstance(names, str) else names
	if not names:
		frappe.throw(_("Select at least one document."))
	if not frappe.db.exists("WhatsApp Instance", instance):
		frappe.throw(_("WhatsApp Instance {0} not found").format(instance))
	for name in names:
		frappe.has_permission(doctype, "print", name, throw=True)

	kwargs = dict(
		doctype=doctype, names=names, instance=instance, print_format=print_format,
		message=message, phone=phone if len(names) == 1 else None,
		no_letterhead=frappe.utils.cint(no_letterhead),
	)
	if len(names) > SYNC_LIMIT:
		frappe.enqueue(
			"notifier.send._send_documents", queue="long", timeout=3600,
			notify_user=frappe.session.user, **kwargs,
		)
		return {"queued": True, "count": len(names)}
	return _send_documents(**kwargs)


def _send_documents(doctype, names, instance, print_format=None, message=None, phone=None,
		no_letterhead=0, notify_user=None):
	sent, failed = [], []
	for name in names:
		try:
			doc = frappe.get_doc(doctype, name)
			to = phone or get_party_phone(doc)
			if not to:
				raise frappe.ValidationError(_("no phone number found"))

			body = frappe.render_template(message, {"doc": doc}).strip() if message else ""
			pdf_url = build_pdf_file(doc, print_format, no_letterhead=no_letterhead)

			if body:
				_queue_message(instance, to, "text", message=body, label=name)
			_queue_message(instance, to, "document", attach=pdf_url, label=name)

			doc.add_comment(
				"Info",
				_("PDF ({0}) sent on WhatsApp to {1} via {2}").format(
					print_format or "Standard", to, instance
				),
			)
			frappe.db.commit()
			sent.append({"name": name, "phone": to})
		except Exception as e:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"Send WhatsApp failed: {doctype} {name}")
			failed.append({"name": name, "error": frappe.utils.strip_html_tags(str(e))[:300]})

	result = {"sent": sent, "failed": failed}
	if notify_user:
		frappe.publish_realtime("notifier_whatsapp_sent", result, user=notify_user)
	return result
