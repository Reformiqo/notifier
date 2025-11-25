import frappe
import requests
import base64
from frappe.utils.file_manager import save_file

@frappe.whitelist(allow_guest=True)
def connect_instance(instance):
    settings = frappe.get_doc("Evolution API Settings")
    base_url = settings.base_url
    api_key = settings.api_token

    url = f"{base_url}/instance/connect/{instance}"

    headers = {"apikey": api_key}

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        frappe.throw(f"API request failed with status {response.status_code}")
    
    response_data = response.json()
    base64_data = response_data.get("base64")
    
    if not base64_data:
        frappe.throw("No base64 data received from API")
    
    # Create data dictionary with required fields
    data = {
        "base64": base64_data,
        "instance": instance
    }
    
    return save_base64_image_as_file(data)


@frappe.whitelist(allow_guest=True)
def save_base64_image_as_file(data):
    try:
        # Check if data is a dictionary and has required fields
        if not isinstance(data, dict):
            frappe.throw("Data must be a dictionary")
            
        if "base64" not in data or not data["base64"]:
            frappe.throw("Base64 data is required")
            
        if "instance" not in data or not data["instance"]:
            frappe.throw("Instance is required")
        
        base64_string = data["base64"]
        instance_name = data["instance"]
        
        # Clean the base64 string
        if base64_string.startswith('data:'):
            # Extract just the base64 part after the comma
            base64_string = base64_string.split(',')[1]
        
        # Remove any whitespace/newlines
        base64_string = base64_string.strip().replace('\n', '').replace('\r', '')
        
        # Decode base64 string to bytes
        file_content = base64.b64decode(base64_string)
        
        # Validate that we have actual image data
        if len(file_content) == 0:
            raise ValueError("Decoded file content is empty")
        
        # Generate filename with timestamp to avoid conflicts
        import time
        timestamp = int(time.time())
        filename = f"{instance_name}_{timestamp}.png"
        
        # Save file using Frappe's file manager
        file_doc = save_file(
            fname=filename,
            content=file_content,
            dt="WhatsApp Instance",
            dn=instance_name,
            is_private=0,
        )
        
        # Update the WhatsApp Instance with the new QR code
        frappe.db.set_value("WhatsApp Instance", instance_name, "qr_code", file_doc.file_url)
        
        frappe.db.commit()
        return {
            "success": True,
            "file_url": file_doc.file_url,
            "message": "QR code saved successfully"
        }
        
    except base64.binascii.Error as e:
        frappe.log_error(f"Base64 decode error: {str(e)}", "Base64 Decode Error")
        frappe.throw(f"Invalid base64 data: {str(e)}")
    except Exception as e:
        frappe.log_error(f"Error saving base64 image: {str(e)}", "Base64 Image Save Error")
        frappe.throw(f"Failed to save image: {str(e)}")

@frappe.whitelist(allow_guest=True)
def get_instance_status(instance):
    settings = frappe.get_doc("Evolution API Settings")
    base_url = settings.base_url
    api_key = settings.api_token

    url = f"{base_url}/instance/connectionState/{instance}"

    headers = {"apikey": api_key}

    response = requests.get(url, headers=headers)
    # "instance": {
    #   "instanceName": "Abdoulie Bah (2206084445)",
    #   "state": "open"
    # }
    instance_name = response.json().get("instance").get("instanceName")
    state = response.json().get("instance").get("state")

    if state == "open":
        frappe.db.set_value("WhatsApp Instance", instance_name, "status", "Open")
        # remove the qr code 
        frappe.db.set_value("WhatsApp Instance", instance_name, "qr_code", None)
        frappe.db.commit()

    

    return response.json()
    
    
@frappe.whitelist(allow_guest=True)
def create_instance(instance, phone_number, token):
    settings = frappe.get_doc("Evolution API Settings")
    base_url = settings.base_url
    api_key = settings.api_token

    url = f"{base_url}/instance/create"


    payload = {
        "instanceName": instance,
        "token": token,
        "qrcode": True,
        "number": phone_number,
        "integration": "WHATSAPP-BAILEYS",
        "rejectCall": True,
        "msgCall": "false",
        "groupsIgnore": True,
        "alwaysOnline": True,
        "readMessages": True,
        "readStatus": True,
        
    }
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()