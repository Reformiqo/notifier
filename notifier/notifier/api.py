import frappe
from frappe import _

@frappe.whitelist()
def get_whatsapp_broadcasts():
	"""Get list of WhatsApp broadcasts"""
	try:
		broadcasts = frappe.get_all("WhatsApp Broadcast", 
			fields=["name", "broadcast_name", "template", "group", "status", "sent_count", "failed_count"],
			order_by="creation desc"
		)
		return broadcasts
	except Exception as e:
		frappe.log_error(f"Get Broadcasts API Error: {str(e)}")
		return []

@frappe.whitelist()
def get_whatsapp_templates():
	"""Get list of WhatsApp templates"""
	try:
		templates = frappe.get_all("WhatsApp Templates", 
			fields=["name", "actual_name"],
			order_by="name"
		)
		return templates
	except Exception as e:
		frappe.log_error(f"Get Templates API Error: {str(e)}")
		return []

@frappe.whitelist()
def get_template_details(template_name):
	"""Get detailed template information for preview"""
	try:
		template = frappe.get_doc("WhatsApp Templates", template_name)
		return {
			"name": template.name,
			"header": template.header if hasattr(template, 'header') else None,
			"body": template.body if hasattr(template, 'body') else None,
			"footer": template.footer if hasattr(template, 'footer') else None,
			"status": template.status if hasattr(template, 'status') else None
		}
	except Exception as e:
		frappe.log_error(f"Get Template Details API Error: {str(e)}")
		return None

@frappe.whitelist()
def get_contact_groups():
	"""Get list of contact groups"""
	try:
		groups = frappe.get_all("Contact Group", 
			fields=["name"],
			order_by="name"
		)
		return groups
	except Exception as e:
		frappe.log_error(f"Get Groups API Error: {str(e)}")
		return []

@frappe.whitelist()
def create_whatsapp_broadcast(broadcast_name, template, group, scheduled_time=None):
	"""Create a new WhatsApp broadcast"""
	try:
		broadcast = frappe.new_doc("WhatsApp Broadcast")
		broadcast.broadcast_name = broadcast_name
		broadcast.template = template
		broadcast.group = group
		if scheduled_time:
			broadcast.scheduled_time = scheduled_time
		broadcast.status = "Draft"
		broadcast.save()
		
		return {"success": True, "message": "Broadcast created successfully", "name": broadcast.name}
	except Exception as e:
		frappe.log_error(f"Create Broadcast API Error: {str(e)}")
		return {"success": False, "error": str(e)}

@frappe.whitelist()
def send_whatsapp_broadcast(broadcast_name):
	"""Send a WhatsApp broadcast"""
	try:
		broadcast = frappe.get_doc("WhatsApp Broadcast", broadcast_name)
		broadcast.send_broadcast()
		return {"success": True, "message": "Broadcast sent successfully"}
	except Exception as e:
		frappe.log_error(f"Broadcast API Error: {str(e)}")
		return {"success": False, "error": str(e)} 