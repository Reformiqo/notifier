"""Re-apply the WhatsApp Notification channel setup (idempotent).

Frappe patches run once. Some sites migrated with ``setup_whatsapp_notification``
/ ``setup_whatsapp_group_channel`` recorded as done but the channel option and
custom fields did not take effect (e.g. a stale meta cache at migrate time). A
normal re-migrate will not re-run a completed patch, so this new patch re-applies
them forcefully and clears the Notification cache.
"""

import frappe

from notifier.patches import setup_whatsapp_notification, setup_whatsapp_group_channel


def execute():
    setup_whatsapp_notification.execute()
    setup_whatsapp_group_channel.execute()
    frappe.clear_cache(doctype="Notification")
