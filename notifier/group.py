"""Group helpers backed by WuzAPI (whatsmeow)."""

import frappe

from notifier import wuzapi


@frappe.whitelist()
def get_groups(instance):
    """Return the raw WuzAPI group list for ``instance``."""
    token = wuzapi.instance_token(instance)
    if not token:
        frappe.throw(f"No WuzAPI token stored for instance {instance}")
    return wuzapi.get_groups(token)


@frappe.whitelist()
def get_groups_with_contacts(instance):
    """Group list with each participant's JID resolved to a bare phone number."""
    data = get_groups(instance)
    groups = (data.get("data") or {}).get("Groups", []) if isinstance(data, dict) else []

    for group in groups:
        group["resolved_participants"] = [
            {
                "jid": p.get("JID"),
                "actual_phone": wuzapi.phone_from_jid(p.get("JID")),
                "is_admin": bool(p.get("IsAdmin") or p.get("IsSuperAdmin")),
            }
            for p in group.get("Participants", [])
        ]

    return data


@frappe.whitelist()
def get_group_participants_detailed(instance, group_id):
    """Detailed participant info for a single group."""
    data = get_groups_with_contacts(instance)
    groups = (data.get("data") or {}).get("Groups", []) if isinstance(data, dict) else []

    target = next((g for g in groups if g.get("JID") == group_id), None)
    if not target:
        return {"error": "Group not found"}

    participants = target.get("resolved_participants", [])
    return {
        "group_info": {"jid": target.get("JID"), "name": target.get("Name")},
        "participants": participants,
        "summary": {
            "total_participants": len(participants),
            "resolved_phones": len([p for p in participants if p["actual_phone"]]),
        },
    }
