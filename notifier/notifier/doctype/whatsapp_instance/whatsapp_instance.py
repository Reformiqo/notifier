# Copyright (c) 2025, royalsmb and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import uuid
import requests
from datetime import datetime
import base64
from frappe.utils.file_manager import save_file
from notifier.api import create_instance

base_url = frappe.db.get_single_value("Evolution API Settings", "base_url")
api_token = frappe.db.get_single_value("Evolution API Settings", "api_token")


class WhatsAppInstance(Document):
    def validate(self):

        token = str(uuid.uuid4())
        self.token = token

    def after_insert(self):
        # Note: phone_number field might need to be added to the doctype if not present
        phone_number = getattr(self, "phone_number", None) or self.name
        create_instance(self.name, phone_number, self.token)


@frappe.whitelist(allow_guest=True)
def get_instance(instance_name=None):

    if not instance_name:
        frappe.throw("Instance name is required")

    try:
        url = f"{base_url}/instance/connect/{instance_name}"
        headers = {"apikey": api_token}

        # Make the API request
        response = requests.get(url, headers=headers, timeout=30)

        # Log the response for debugging
        frappe.logger().info(f"API Response Status: {response.status_code}")
        frappe.logger().info(f"API Response Headers: {response.headers}")

        response.raise_for_status()  # Raise an exception for bad status codes

        response_data = response.json()
        frappe.logger().info(f"API Response Data: {response_data}")

        base64_image = response_data.get("base64")

        if not base64_image:
            # Log the full response for debugging
            frappe.logger().error(
                f"No base64 image in response. Full response: {response_data}"
            )
            frappe.throw(
                f"No base64 image received from API. Response: {response_data}"
            )

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qrcode_{timestamp}.png"

        # Save the image
        doctype = "WhatsApp Instance"
        docname = instance_name
        file_doc = save_base64_image_to_file(base64_image, filename, doctype, docname)

        return {
            "base64": base64_image,
            "file_url": file_doc.file_url if file_doc else None,
            "filename": filename,
            "full_response": response_data,
        }

    except requests.exceptions.RequestException as e:
        frappe.log_error(
            f"API Request Error for instance {instance_name}: {str(e)}",
            "Evolution API Error",
        )
        frappe.throw(
            f"Failed to connect to Evolution API for instance {instance_name}: {str(e)}"
        )
    except Exception as e:
        frappe.log_error(
            f"Unexpected Error for instance {instance_name}: {str(e)}",
            "QR Code Generation Error",
        )
        frappe.throw(f"An error occurred for instance {instance_name}: {str(e)}")


def save_base64_image_to_file(
    base64_string,
    filename,
    doctype=None,
    docname=None,
    folder=None,
    is_private=0,
    instance_name=None,
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
        frappe.db.set_value(doctype, docname, "qr_code", file_doc.file_url)

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
def refresh_qr_code(instance_name=None):
    """Force refresh QR code by clearing any cache"""

    if not instance_name:
        frappe.throw("Instance name is required")

    try:
        # First, try to disconnect/reset the instance (if API supports it)
        disconnect_url = f"{base_url}/instance/logout/{instance_name}"
        headers = {"apikey": api_token}

        # Attempt to logout/disconnect first
        try:
            requests.delete(disconnect_url, headers=headers, timeout=10)
        except:
            pass  # Ignore if disconnect fails

        # Wait a moment
        import time

        time.sleep(2)

        # Now get fresh QR code
        return get_instance(instance_name)

    except Exception as e:
        frappe.log_error(f"Error refreshing QR code: {str(e)}", "QR Code Refresh Error")
        return get_instance(instance_name)  # Fallback to normal method


# Method to check instance status
@frappe.whitelist(allow_guest=True)
def check_instance_status(instance_name=None):
    """Check the current status of the WhatsApp instance"""

    if not instance_name:
        frappe.throw("Instance name is required")

    try:
        url = f"{base_url}/instance/fetchInstances/{instance_name}"
        headers = {"apikey": api_token}

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        frappe.log_error(
            f"Error checking instance status: {str(e)}", "Instance Status Error"
        )
        frappe.throw(f"Failed to check instance status: {str(e)}")


@frappe.whitelist(allow_guest=True)
def connect_instance(instance):
    try:
        settings = frappe.get_doc("Evolution API Settings")
        api_base_url = settings.base_url
        api_key = settings.api_token
        headers = {"apikey": api_key}

        # Try different possible endpoints for QR code generation
        endpoints_to_try = [
            f"/instance/connect/{instance}",
            f"/instance/qrcode/{instance}",
            f"/instance/{instance}/qrcode",
            f"/instance/{instance}/connect",
        ]

        response = None
        successful_url = None

        for endpoint in endpoints_to_try:
            url = f"{api_base_url}{endpoint}"
            frappe.logger().info(f"Trying endpoint: {url}")

            try:
                response = requests.get(url, headers=headers, timeout=30)
                frappe.logger().info(
                    f"Response status for {endpoint}: {response.status_code}"
                )

                if response.status_code == 200:
                    successful_url = url
                    break
                elif response.status_code == 404:
                    frappe.logger().info(
                        f"Endpoint {endpoint} not found, trying next..."
                    )
                    continue
                else:
                    frappe.logger().info(
                        f"Endpoint {endpoint} returned {response.status_code}"
                    )

            except requests.exceptions.RequestException as e:
                frappe.logger().info(f"Failed to connect to {endpoint}: {str(e)}")
                continue

        if not response or response.status_code != 200:
            if response:
                frappe.logger().info(f"Final response status: {response.status_code}")
                frappe.logger().info(f"Final response content: {response.text[:500]}")

                # If we get 404, try to create the instance first
                if response.status_code == 404:
                    frappe.logger().info(
                        "Instance not found, attempting to create it first..."
                    )
                    try:
                        create_url = f"{api_base_url}/instance/create"
                        create_data = {
                            "instanceName": instance,
                            "qrcode": True,
                            "integration": "WHATSAPP-BAILEYS",
                        }
                        create_response = requests.post(
                            create_url, headers=headers, json=create_data, timeout=30
                        )
                        frappe.logger().info(
                            f"Create instance response: {create_response.status_code}"
                        )

                        if create_response.status_code in [200, 201]:
                            # Now try to get QR code again
                            import time

                            time.sleep(2)  # Wait a moment for instance to initialize

                            for endpoint in endpoints_to_try:
                                url = f"{api_base_url}{endpoint}"
                                response = requests.get(
                                    url, headers=headers, timeout=30
                                )
                                if response.status_code == 200:
                                    successful_url = url
                                    break
                    except Exception as create_error:
                        frappe.logger().info(
                            f"Failed to create instance: {str(create_error)}"
                        )

                if not response or response.status_code != 200:
                    frappe.throw(
                        f"Could not get QR code from Evolution API. Last status: {response.status_code if response else 'No response'}"
                    )
            else:
                frappe.throw(
                    "Could not connect to any Evolution API endpoint for QR code generation"
                )

        frappe.logger().info(f"Successfully connected using: {successful_url}")
        frappe.logger().info(
            f"Response content: {response.text[:500]}"
        )  # Log first 500 chars

        response_data = response.json()

        # Log the complete response structure for debugging
        frappe.logger().info(f"Complete API response: {response_data}")

        # Check different possible response formats
        base64_data = None
        if isinstance(response_data, dict):
            # Try different possible keys for base64 data
            base64_data = (
                response_data.get("base64")
                or response_data.get("qrcode")
                or response_data.get("qr")
                or response_data.get("code")
            )

            # If it's nested in a data object
            if not base64_data and "data" in response_data:
                data_obj = response_data.get("data", {})
                base64_data = (
                    data_obj.get("base64")
                    or data_obj.get("qrcode")
                    or data_obj.get("qr")
                    or data_obj.get("code")
                )

        frappe.logger().info(f"Extracted base64_data: {bool(base64_data)}")

        if not base64_data:
            # Provide detailed error with actual response structure
            response_keys = (
                list(response_data.keys())
                if isinstance(response_data, dict)
                else "Not a dictionary"
            )
            frappe.throw(
                f"No base64 data received from API. Response structure: {response_keys}. Full response: {response_data}"
            )

        # Use the updated function to save the QR code
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qrcode_{instance}_{timestamp}.png"

        file_doc = save_base64_image_to_file(
            base64_data, filename, doctype="WhatsApp Instance", docname=instance
        )

        return {
            "success": True,
            "file_url": file_doc.file_url,
            "message": "QR code generated successfully",
        }

    except requests.exceptions.Timeout:
        frappe.throw(
            "Connection timeout. The Evolution API server is taking too long to respond."
        )
    except requests.exceptions.ConnectionError:
        frappe.throw(
            "Cannot connect to Evolution API server. Please check the base URL in Evolution API Settings."
        )
    except Exception as e:
        frappe.log_error(
            f"Error in connect_instance: {str(e)}", "Connect Instance Error"
        )
        frappe.throw(f"Failed to connect instance: {str(e)}")


# Duplicate function removed - functionality consolidated into save_base64_image_to_file


@frappe.whitelist(allow_guest=True)
def get_instance_status(instance):
    settings = frappe.get_doc("Evolution API Settings")
    api_base_url = settings.base_url
    api_key = settings.api_token

    url = f"{api_base_url}/instance/connectionState/{instance}"

    headers = {"apikey": api_key}

    response = requests.get(url, headers=headers, timeout=30)
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
