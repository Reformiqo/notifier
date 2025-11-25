import frappe
import requests
@frappe.whitelist(allow_guest=True)
def check_instance_status():
    try:
        base_url = frappe.db.get_single_value("Evolution API Settings", "base_url")
        api_token = frappe.db.get_single_value("Evolution API Settings", "api_token")

        
        instances = frappe.db.get_list("WhatsApp Instance", fields=["name", "phone_number"])
        
        for instance in instances:
            
            url = f"{base_url}/instance/connectionState/{instance.name}"
            headers = {"apikey": api_token}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            if response.json().get("status") == "404":
                continue
            
            if response.json().get("instance").get("state") == "open":
                frappe.db.set_value("WhatsApp Instance", instance.name, "status", "Open")
                frappe.db.commit()
            elif response.json().get("instance").get("state") == "close":
                frappe.db.set_value("WhatsApp Instance", instance.name, "status", "Closed")
                frappe.db.commit()
            else:
                frappe.db.set_value("WhatsApp Instance", instance.name, "status", "Connecting")
                frappe.db.commit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Instance Status Error")


@frappe.whitelist(allow_guest=True)
def update_instance_status(instance, status):
    try:
        frappe.set_user("Administrator")
        if frappe.db.exists("WhatsApp Instance", instance):
            if status == "open":
                frappe.db.set_value("WhatsApp Instance", instance, "status", "Open", update_modified=False)
            elif status == "close":
                frappe.db.set_value("WhatsApp Instance", instance, "status", "Closed", update_modified=False)
            elif status == "connecting":
                frappe.db.set_value("WhatsApp Instance", instance, "status", "Connecting", update_modified=False)
            frappe.db.commit()
        return True
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Instance Status Error")
        return False