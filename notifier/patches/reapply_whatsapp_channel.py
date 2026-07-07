"""Re-apply the WhatsApp Notification channel setup (idempotent).

Delegates to notifier.setup (also run from after_install / after_migrate hooks).
"""

from notifier.setup import setup_notification_channel


def execute():
    setup_notification_channel()
