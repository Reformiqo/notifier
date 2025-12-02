import frappe
import requests
import uuid
import base64
import os
from frappe.utils.file_manager import save_file
from datetime import datetime


base_url = frappe.db.get_single_value("Evolution API Settings", "base_url")
api_token = frappe.db.get_single_value("Evolution API Settings", "api_token")


def get_base_url():
    """Get Evolution API base URL from settings"""
    try:
        return frappe.db.get_single_value("Evolution API Settings", "base_url")
    except Exception:
        return None


def get_api_token():
    """Get Evolution API token from settings"""
    try:
        return frappe.db.get_single_value("Evolution API Settings", "api_token")
    except Exception:
        return None


@frappe.whitelist(allow_guest=True)
def send_text_message(instance, phone, message):
    base_url = get_base_url()
    api_token = get_api_token()
    url = f"{base_url}/message/sendText/{instance}"

    payload = {
        "number": phone,
        "text": message,
        "linkPreview": True,
    }
    headers = {"apikey": api_token, "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


@frappe.whitelist(allow_guest=True)
def send_media_message(docname):
    doc = frappe.get_doc("WhatsApp Message", docname)
    phone = "919033230370"
    media_type = doc.content_type
    mimetype = f"image/{doc.attach.split('.')[-1]}"
    caption = doc.message

    media = frappe.utils.get_url(doc.attach).replace(" ", "%20")
    file_name = doc.label

    url = f"{base_url}/message/sendMedia/{doc.instance}"

    payload = {
        "number": phone,
        "mediatype": media_type,
        "mimetype": mimetype,
        "caption": caption,
        "media": media,
        "fileName": file_name,
        "linkPreview": True,
    }
    headers = {"apikey": api_token, "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


@frappe.whitelist(allow_guest=True)
def send_audio_message(instance):
    phone = "2206084445"
    audio = "https://backend.jokoor.com/files/114.mp3"

    base_url = get_base_url()
    api_token = get_api_token()
    url = f"{base_url}/message/sendWhatsAppAudio/{instance}"

    payload = {
        "number": phone,
        "audio": audio,
        "linkPreview": True,
    }
    headers = {"apikey": api_token, "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


@frappe.whitelist(allow_guest=True)
def send_contact_message(instance):
    phone = "2206084445"
    base_url = get_base_url()
    api_token = get_api_token()
    url = f"{base_url}/message/sendContact/{instance}"

    payload = {
        "number": phone,
        "contact": [
            {
                "fullName": "Momodou Kh",
                "wuid": "1234567890",
                "phoneNumber": "2206084445",
                "organization": "Jokoor",
                "email": "momodoukh@gmail.com",
                "url": "https://www.google.com",
            }
        ],
    }
    headers = {"apikey": api_token, "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


@frappe.whitelist(allow_guest=True)
def send_poll_message(instance):
    phone = "2206084445"
    base_url = get_base_url()
    api_token = get_api_token()
    url = f"{base_url}/message/sendPoll/{instance}"

    payload = {
        "number": phone,
        "name": "Test Poll",
        "selectableCount": 1,
        "values": ["Question 1", "Question 2", "Question 3"],
        "linkPreview": True,
    }
    headers = {"apikey": api_token, "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


@frappe.whitelist(allow_guest=True)
def send_list_message(instance):
    phone = "2206084445"
    base_url = get_base_url()
    api_token = get_api_token()
    url = f"{base_url}/message/sendList/{instance}"

    payload = {
        "number": phone,
        "title": "Test List",
        "description": "Test Description",
        "buttonText": "Test Button",
        "footerText": "Test Footer",
        "values": [
            {
                "title": "Test List",
                "rows": [
                    {
                        "title": "Test List",
                        "description": "Test Description",
                        "rowId": "1234567890",
                    }
                ],
            }
        ],
        "sections": [
            {
                "title": "Test Section",
                "rows": [
                    {
                        "title": "Test Section",
                        "description": "Test Description",
                        "rowId": "1234567890",
                    }
                ],
            }
        ],
        "linkPreview": True,
    }
    headers = {"apikey": api_token, "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


@frappe.whitelist(allow_guest=True)
def send_button_message(instance):
    phone = "2206084445"
    base_url = get_base_url()
    api_token = get_api_token()
    url = f"{base_url}/message/sendButtons/{instance}"

    payload = {
        "number": phone,
        "title": "Test Button",
        "description": "Test Description",
        "footer": "Test Footer",
        "buttons": [
            {
                "type": "reply",
                "title": "Test Button",
                "displayText": "Test Display Text",
                "id": "1234567890",
            }
        ],
        "linkPreview": True,
    }
    headers = {"apikey": api_token, "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.json()


@frappe.whitelist(allow_guest=True)
def create_instance(instance, phone_number, token):
    try:
        base_url = get_base_url()
        api_token = get_api_token()
        phone = phone_number.replace("+", "")

        url = f"{base_url}/instance/create"

        payload = {
            "instanceName": instance,
            "token": token,
            "qrcode": True,
            "number": phone,
            "integration": "WHATSAPP-BAILEYS",
            "rejectCall": False,
            "groupsIgnore": False,
            "alwaysOnline": True,
            "readMessages": True,
            "readStatus": True,
            "syncFullHistory": True,
        }
        headers = {"apikey": api_token, "Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Raise exception for HTTP errors

        return response.json()
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
        frappe.log_error(error_msg, "Evolution API HTTP Error")
        frappe.throw(f"Failed to create instance: {error_msg}")
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        frappe.log_error(error_msg, "Evolution API Request Error")
        frappe.throw(f"Network error: {error_msg}")
    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        frappe.log_error(frappe.get_traceback(), "Evolution API Error")
        frappe.throw(f"An error occurred: {error_msg}")


@frappe.whitelist(allow_guest=True)
def get_instance(instance_name: str, phone_number: str = None):
    """
    Get instance connection details including QR code and pairing information

    Args:
        instance_name (str): Name of the WhatsApp instance
        phone_number (str, optional): Phone number with country code

    Returns:
        dict: Instance connection details including pairingCode, code, and count
    """
    try:
        base_url = get_base_url()
        api_token = get_api_token()
        # First check if the instance exists and its connection state
        conn_status = connection_status(instance_name)

        # Build URL with optional phone number parameter
        url = f"{base_url}/instance/connect/{instance_name}"
        if phone_number:
            # Clean phone number (remove + if present)
            clean_phone = phone_number.replace("+", "")
            url += f"?number={clean_phone}"

        headers = {"apikey": api_token}

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise exception for HTTP errors

        result = response.json()

        # Validate response structure
        if not isinstance(result, dict):
            frappe.throw("Invalid response format from Evolution API")

        # Check if we got meaningful data
        if result.get("count") == 0:
            frappe.msgprint(
                "Instance connection returned empty result. The instance might not be properly initialized or connected."
            )

        # Log the response for debugging
        frappe.logger().info("Instance connection response: %s", result)

        return result

    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
        frappe.log_error(error_msg, "Evolution API HTTP Error")
        frappe.throw(f"Failed to connect to instance: {error_msg}")
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        frappe.log_error(error_msg, "Evolution API Request Error")
        frappe.throw(f"Network error: {error_msg}")
    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        frappe.log_error(frappe.get_traceback(), "Evolution API Error")
        frappe.throw(f"An error occurred: {error_msg}")


@frappe.whitelist(allow_guest=True)
def get_attachment_as_base64(docname, doctype="WhatsApp Message"):
    """
    Get the attachment from a document and convert it to base64 string

    Args:
        docname (str): Name of the document
        doctype (str): Type of the document (default: "WhatsApp Message")

    Returns:
        str: Base64 encoded string of the file content, or None if no attachment
    """
    try:
        # Get the document
        doc = frappe.get_doc(doctype, docname)

        # Check if attach field exists and has a value
        if not hasattr(doc, "attach") or not doc.attach:
            frappe.throw("No attachment found in the document")

        # Get the file path from attach field
        file_path = doc.attach

        # Find the File document
        # First try to get it by attached_to (most reliable)
        file_doc = None
        file_docs = frappe.get_all(
            "File",
            filters={"attached_to_doctype": doctype, "attached_to_name": docname},
            fields=["name"],
            order_by="creation desc",
            limit=1,
        )
        if file_docs:
            file_doc = frappe.get_doc("File", file_docs[0].name)

        # If file_doc not found, try to get it by file_url
        if not file_doc:
            # Ensure file_path has leading slash for file_url search
            search_path = file_path if file_path.startswith("/") else f"/{file_path}"
            file_docs = frappe.get_all(
                "File", filters={"file_url": search_path}, fields=["name"], limit=1
            )
            if file_docs:
                file_doc = frappe.get_doc("File", file_docs[0].name)

        if not file_doc:
            frappe.throw(f"File not found for attachment: {doc.attach}")

        # Get file content as bytes
        file_content = file_doc.get_content()

        # If content is string, encode it to bytes
        if isinstance(file_content, str):
            file_content = file_content.encode("utf-8")

        # Convert to base64
        base64_string = base64.b64encode(file_content).decode("utf-8")

        return base64_string

    except Exception as e:
        frappe.log_error(
            f"Error converting attachment to base64: {str(e)}",
            "Attachment to Base64 Error",
        )
        frappe.throw(f"Failed to convert attachment to base64: {str(e)}")


def save_base64_image_as_file(
    base64_string, filename, doctype=None, docname=None, folder=None, is_private=0
):
    try:
        # Clean the base64 string
        if base64_string.startswith("data:"):
            # Extract just the base64 part after the comma
            base64_string = base64_string.split(",")[1]

        # Remove any whitespace/newlines
        base64_string = base64_string.strip().replace("\n", "").replace("\r", "")

        # Decode base64 string to bytes
        file_content = base64.b64decode(base64_string)

        # Validate that we have actual image data
        if len(file_content) == 0:
            raise ValueError("Decoded file content is empty")

        # Save file using Frappe's file manager
        file_doc = save_file(
            fname=filename,
            content=file_content,
            dt=doctype,
            dn=docname,
            folder=folder,
            is_private=is_private,
        )

        frappe.db.commit()
        return file_doc

    except base64.binascii.Error as e:
        frappe.log_error(f"Base64 decode error: {str(e)}", "Base64 Decode Error")
        frappe.throw(f"Invalid base64 data: {str(e)}")
    except Exception as e:
        frappe.log_error(
            f"Error saving base64 image: {str(e)}", "Base64 Image Save Error"
        )
        frappe.throw(f"Failed to save image: {str(e)}")


# Alternative method to force refresh the QR code
@frappe.whitelist(allow_guest=True)
def refresh_qr_code(instance):

    try:
        base_url = get_base_url()
        api_token = get_api_token()
        # First, try to disconnect/reset the instance (if API supports it)
        disconnect_url = f"{base_url}/instance/logout/{instance}"
        headers = {"apikey": api_token}

        # Attempt to logout/disconnect first
        try:
            requests.delete(disconnect_url, headers=headers)
        except:
            pass  # Ignore if disconnect fails

        # Wait a moment
        import time

        time.sleep(2)

        # Now get fresh QR code
        return get_instance(instance)

    except Exception as e:
        frappe.log_error(f"Error refreshing QR code: {str(e)}", "QR Code Refresh Error")
        return get_instance(instance)  # Fallback to normal method


# Method to check instance status
@frappe.whitelist(allow_guest=True)
def check_instance_status():
    """Check the current status of the WhatsApp instance"""

    try:
        base_url = get_base_url()
        api_token = get_api_token()
        url = f"{base_url}/instance/fetchInstances"
        headers = {"apikey": api_token}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        frappe.log_error(
            f"Error checking instance status: {str(e)}", "Instance Status Error"
        )
        frappe.throw(f"Failed to check instance status: {str(e)}")


@frappe.whitelist(allow_guest=True)
def connection_status(instance_name):
    """
    Check the connection status of a WhatsApp instance

    Args:
        instance_name (str): Name of the WhatsApp instance

    Returns:
        dict: Connection status information
    """
    try:
        base_url = get_base_url()
        api_token = get_api_token()
        url = f"{base_url}/instance/connectionState/{instance_name}"
        headers = {"apikey": api_token}

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        result = response.json()
        frappe.logger().info("Connection status for %s: %s", instance_name, result)

        return result

    except Exception as e:
        frappe.log_error(
            f"Error checking connection status: {str(e)}", "Connection Status Error"
        )
        return {"error": str(e), "state": "unknown"}


@frappe.whitelist(allow_guest=True)
def diagnose_instance_connection(instance_name, phone_number=None):
    """
    Comprehensive diagnosis of instance connection issues

    Args:
        instance_name (str): Name of the WhatsApp instance
        phone_number (str, optional): Phone number with country code

    Returns:
        dict: Detailed diagnosis information
    """
    diagnosis = {
        "instance_name": instance_name,
        "phone_number": phone_number,
        "checks": {},
        "recommendations": [],
    }

    try:
        # Check 1: Connection Status
        try:
            conn_status = connection_status(instance_name)
            diagnosis["checks"]["connection_status"] = conn_status

            if conn_status.get("state") == "open":
                diagnosis["recommendations"].append(
                    "Instance is connected. Try refreshing the QR code."
                )
            elif conn_status.get("state") == "connecting":
                diagnosis["recommendations"].append(
                    "Instance is connecting. Wait a moment and try again."
                )
            elif conn_status.get("state") == "close":
                diagnosis["recommendations"].append(
                    "Instance is disconnected. You need to reconnect."
                )
            else:
                diagnosis["recommendations"].append(
                    f"Unknown connection state: {conn_status.get('state')}"
                )

        except Exception as e:
            diagnosis["checks"]["connection_status"] = {"error": str(e)}
            diagnosis["recommendations"].append(
                "Could not check connection status. Verify instance name and API credentials."
            )

        # Check 2: Instance Fetch
        try:
            base_url = get_base_url()
            api_token = get_api_token()
            fetch_url = f"{base_url}/instance/fetchInstances/{instance_name}"
            headers = {"apikey": api_token}
            response = requests.get(fetch_url, headers=headers)
            diagnosis["checks"]["instance_fetch"] = response.json()
        except Exception as e:
            diagnosis["checks"]["instance_fetch"] = {"error": str(e)}
            diagnosis["recommendations"].append(
                "Could not fetch instance details. Instance might not exist."
            )

        # Check 3: Try to get instance connection
        try:
            instance_result = get_instance(instance_name, phone_number)
            diagnosis["checks"]["instance_connection"] = instance_result

            if instance_result.get("count") == 0:
                diagnosis["recommendations"].append(
                    "Instance connection returned count=0. This usually means:"
                )
                diagnosis["recommendations"].append(
                    "- Instance is not properly initialized"
                )
                diagnosis["recommendations"].append("- Instance needs to be recreated")
                diagnosis["recommendations"].append(
                    "- Phone number format is incorrect"
                )
                diagnosis["recommendations"].append(
                    "- Instance is already connected elsewhere"
                )
            elif instance_result.get("pairingCode"):
                diagnosis["recommendations"].append(
                    "Pairing code available. Use this to connect your device."
                )
            elif instance_result.get("code"):
                diagnosis["recommendations"].append(
                    "QR code available. Scan with WhatsApp to connect."
                )

        except Exception as e:
            diagnosis["checks"]["instance_connection"] = {"error": str(e)}
            diagnosis["recommendations"].append(
                f"Failed to get instance connection: {str(e)}"
            )

        return diagnosis

    except Exception as e:
        frappe.log_error(f"Diagnosis error: {str(e)}", "Instance Diagnosis Error")
        return {
            "error": str(e),
            "recommendations": ["Run diagnosis failed. Check logs for details."],
        }


@frappe.whitelist(allow_guest=True)
def get_instance_connection_info(instance_name, phone_number=None):
    """
    Get detailed connection information for an instance including QR code and pairing code

    Args:
        instance_name (str): Name of the WhatsApp instance
        phone_number (str, optional): Phone number with country code

    Returns:
        dict: Connection information with QR code, pairing code, and status
    """
    try:
        # First check connection status
        conn_status = connection_status(instance_name)

        # Get instance connection details
        instance_info = get_instance(instance_name, phone_number)

        # Prepare response
        response = {
            "instance_name": instance_name,
            "connection_status": conn_status,
            "instance_info": instance_info,
            "connection_ready": False,
            "next_steps": [],
        }

        # Analyze the response
        if instance_info.get("count") == 0:
            response["next_steps"].append("Instance created but not connected yet")
            response["next_steps"].append("You need to connect your WhatsApp account")

            # Check if we have a pairing code
            if instance_info.get("pairingCode"):
                response["pairing_code"] = instance_info["pairingCode"]
                response["next_steps"].append(
                    "Use the pairing code to connect your device"
                )
                response["connection_ready"] = True

            # Check if we have a QR code
            if instance_info.get("code"):
                response["qr_code"] = instance_info["code"]
                response["next_steps"].append(
                    "Scan the QR code with WhatsApp to connect"
                )
                response["connection_ready"] = True

            if not response["connection_ready"]:
                response["next_steps"].append(
                    "Try refreshing the QR code or check instance status"
                )

        elif instance_info.get("count") > 0:
            response["connection_ready"] = True
            response["next_steps"].append("Instance appears to be connected")

        return response

    except Exception as e:
        frappe.log_error(
            f"Error getting instance connection info: {str(e)}",
            "Instance Connection Info Error",
        )
        return {
            "error": str(e),
            "next_steps": ["Failed to get connection info. Check logs for details."],
        }


@frappe.whitelist(allow_guest=True)
def force_refresh_instance_connection(instance_name, phone_number=None):
    """
    Force refresh the instance connection to get a new QR code or pairing code

    Args:
        instance_name (str): Name of the WhatsApp instance
        phone_number (str, optional): Phone number with country code

    Returns:
        dict: Updated connection information
    """
    try:
        base_url = get_base_url()
        api_token = get_api_token()
        # First try to logout/disconnect the instance
        logout_url = f"{base_url}/instance/logout/{instance_name}"
        headers = {"apikey": api_token}

        try:
            response = requests.delete(logout_url, headers=headers, timeout=30)
            frappe.logger().info("Logout response: %s", response.status_code)
        except Exception as e:
            frappe.logger().info("Logout failed (this might be normal): %s", str(e))

        # Wait a moment for the logout to process
        import time

        time.sleep(3)

        # Now get fresh connection info
        return get_instance_connection_info(instance_name, phone_number)

    except Exception as e:
        frappe.log_error(
            f"Error refreshing instance connection: {str(e)}", "Instance Refresh Error"
        )
        return {"error": str(e), "message": "Failed to refresh connection. Try again."}


@frappe.whitelist(allow_guest=True)
def wait_for_instance_connection(instance_name, max_wait_time=300, check_interval=10):
    """
    Wait for an instance to become connected

    Args:
        instance_name (str): Name of the WhatsApp instance
        max_wait_time (int): Maximum time to wait in seconds (default: 5 minutes)
        check_interval (int): Time between checks in seconds (default: 10 seconds)

    Returns:
        dict: Final connection status
    """
    import time

    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        try:
            # Check connection status
            conn_status = connection_status(instance_name)

            if conn_status.get("state") == "open":
                return {
                    "connected": True,
                    "status": conn_status,
                    "message": "Instance is now connected!",
                    "wait_time": time.time() - start_time,
                }
            elif conn_status.get("state") == "connecting":
                frappe.logger().info("Instance is connecting... waiting")
            else:
                frappe.logger().info(
                    "Instance state: %s, waiting for connection",
                    conn_status.get("state"),
                )

            time.sleep(check_interval)

        except Exception as e:
            frappe.logger().error("Error checking connection status: %s", str(e))
            time.sleep(check_interval)

    return {
        "connected": False,
        "message": f"Timeout: Instance did not connect within {max_wait_time} seconds",
        "wait_time": time.time() - start_time,
    }


@frappe.whitelist(allow_guest=True)
def get_groups(instance):
    base_url = get_base_url()
    api_token = get_api_token()
    url = f"{base_url}/group/fetchAllGroups/{instance}?getParticipants=false"

    headers = {
        "apikey": api_token,
    }

    response = requests.get(url, headers=headers)

    return response.json()


@frappe.whitelist(allow_guest=True)
def get_instance_token(instance):
    return frappe.db.get_value("WhatsApp Instance", instance, "token")


@frappe.whitelist(allow_guest=True)
def get_contact_list(instance):
    base_url = get_base_url()
    api_token = get_api_token()
    url = f"{base_url}/chat/findContacts/{instance}"
    payload = {"where": {"id": "cmdmoh9av0wlemn4kdk98lr9y"}}

    headers = {"apikey": api_token, "Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers).json()
    for contact in response:
        if not frappe.db.exists("WhatsApp Contact", contact.get("id")):
            doc = frappe.new_doc("WhatsApp Contact")
            doc.full_name = contact.get("pushName")
            doc.phone_number = contact.get("remoteJid")
            doc.image = contact.get("profilePicUrl")
            doc.instance_id = contact.get("instanceId")

            doc.instance = instance
            doc.save()
    frappe.db.commit()

    return response


# @frappe.whitelist(allow_guest=True)
# def get_group(instance):

#     url = f"{base_url}/group/fetchAllGroups/{instance}?getParticipants=true"

#     headers = {
#         "apikey": api_token,
#     }
