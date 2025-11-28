import frappe
import json


@frappe.whitelist(allow_guest=True)
def update_instance():
    try:
        # Get webhook data - can be from form_dict (POST form) or request.json (JSON payload)
        if frappe.request and frappe.request.is_json:
            data = frappe.request.json
        elif hasattr(frappe.local, "form_dict") and frappe.local.form_dict:
            data = frappe.local.form_dict
        else:
            data = {}

        # Log the received data for debugging
        frappe.logger().info("Webhook received: %s", json.dumps(data))

        # Check if this is a connection.update event
        event = data.get("event")
        if event != "connection.update":
            return {"status": "ignored", "message": f"Event {event} not handled"}

        # Extract instance identifier and state
        instance_id = data.get("instance")
        state_data = data.get("data", {})
        state = state_data.get("state")

        if not instance_id:
            frappe.log_error(
                "Instance ID missing in webhook data", "WhatsApp Webhook Error"
            )
            return {"status": "error", "message": "Instance ID missing"}

        if not state:
            frappe.log_error("State missing in webhook data", "WhatsApp Webhook Error")
            return {"status": "error", "message": "State missing"}

        # Find the WhatsApp Instance by document name (instance_id is the document name)
        frappe.set_user("Administrator")
        if not frappe.db.exists("WhatsApp Instance", instance_id):
            frappe.log_error(
                f"WhatsApp Instance not found for instance_id: {instance_id}",
                "WhatsApp Webhook Error",
            )
            return {"status": "error", "message": f"Instance not found: {instance_id}"}

        instance_doc = instance_id

        # Map Evolution API state to Frappe status
        # Evolution API states: "open", "close", "connecting"
        # Frappe statuses: "Open", "Closed", "Connecting"
        status_mapping = {
            "open": "Open",
            "close": "Closed",
            "closed": "Closed",
            "connecting": "Connecting",
        }

        frappe_status = status_mapping.get(state.lower())
        if not frappe_status:
            frappe.log_error(
                f"Unknown state received: {state}", "WhatsApp Webhook Error"
            )
            return {"status": "error", "message": f"Unknown state: {state}"}

        # Update the instance status
        frappe.db.set_value(
            "WhatsApp Instance",
            instance_doc,
            "status",
            frappe_status,
            update_modified=False,
        )
        frappe.db.commit()

        frappe.logger().info(
            "Updated WhatsApp Instance %s status to %s", instance_doc, frappe_status
        )

        return {
            "status": "success",
            "message": f"Instance {instance_doc} status updated to {frappe_status}",
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "WhatsApp Webhook Error")
        return {"status": "error", "message": str(e)}
