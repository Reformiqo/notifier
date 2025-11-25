import frappe
import requests

@frappe.whitelist(allow_guest=True)
def create_instance(doc, method=None):
    try:
        url = "https://n8n.hosting.royalsmb.com/webhook/create-instance"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "doc": doc.as_dict(),
            "doctype": doc.doctype
        }
        requests.post(url, headers=headers, json=data)
        return "OK"
    except Exception as e:  
        frappe.log_error(frappe.get_traceback(), "WhatsApp Webhook Error")
        return "Error"

@frappe.whitelist(allow_guest=True)
def send_message(doc, method=None):
    url = "https://n8n.hosting.royalsmb.com/webhook/92d06cbb-647b-4264-ab07-ee9d9e9cc674"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "doc": doc.as_dict(),
        "doctype": doc.doctype
    }
    requests.post(url, headers=headers, json=data)
    return "OK"

 
