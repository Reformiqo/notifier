"""Anti-ban protection for outbound WhatsApp traffic.

WuzAPI drives a regular WhatsApp account over the unofficial Web protocol, and
WhatsApp bans numbers that behave like bots. The signals it is known to react
to are countered here:

* **Pacing** - bursts of messages with zero gap between them are the clearest
  bot signature. ``pause_between_sends`` sleeps a randomized interval and is
  called between consecutive sends in background jobs (broadcasts, queue
  drain). Single event-driven sends don't need it - they are naturally spaced.
* **Number verification** - messaging numbers that are not on WhatsApp marks
  the sender as a spammer working off a bought/scraped list.
  ``number_exists`` asks WuzAPI's ``/user/check`` and caches the answer.
* **Daily cap** - each instance gets a hard ceiling of sends per day. Messages
  over the cap are parked with status ``Queued`` and drained by the
  ``flush_queued_messages`` scheduled job once room frees up.
* **Warm-up** - fresh numbers that immediately send at volume are banned
  fastest. Instances younger than ~3 weeks get a ramped fraction of the cap.

Everything is configured from the "Anti-Ban Protection" section of WhatsApp
Settings and fails open: an error while checking must never block a send.
"""

import random
import time
from datetime import datetime

import frappe
from frappe.utils import now_datetime, nowdate

from notifier import wuzapi

DEFAULTS = {
    "enable_anti_ban": 1,
    "verify_numbers": 1,
    "min_delay_seconds": 5,
    "max_delay_seconds": 15,
    "daily_message_limit": 200,
    "enable_warmup": 1,
}

# (max age of the instance in days, messages allowed per day)
WARMUP_SCHEDULE = ((3, 20), (7, 50), (14, 100), (21, 150))

NUMBER_CACHE_TTL = 7 * 24 * 3600  # /user/check answers are stable; cache a week
QUEUE_DRAIN_BATCH = 30  # per scheduler run, keeps the job well under its interval


def get_conf():
    """Anti-ban settings with defaults for fields never saved on the Single."""
    settings = frappe.get_cached_doc("WhatsApp Settings")
    conf = frappe._dict()
    for key, fallback in DEFAULTS.items():
        value = settings.get(key)
        conf[key] = fallback if value is None else value
    return conf


def enabled():
    return bool(get_conf().enable_anti_ban)


def sending_paused():
    """True when the global WhatsApp Settings "Enabled" switch is off.

    This is the kill switch: with it off, no message leaves the site -
    dispatch parks everything as Queued and the drain job stays idle. Use it
    while a number is under review by WhatsApp or freshly warmed up.
    """
    return not frappe.db.get_single_value("WhatsApp Settings", "enabled")


# ---------------------------------------------------------------------------
# Pacing
# ---------------------------------------------------------------------------

def pause_between_sends():
    """Sleep a randomized interval. Only call from background jobs."""
    conf = get_conf()
    if not conf.enable_anti_ban:
        return
    low = max(0, int(conf.min_delay_seconds or 0))
    high = max(low, int(conf.max_delay_seconds or 0))
    if high:
        time.sleep(random.uniform(low, high))


# ---------------------------------------------------------------------------
# Daily cap / warm-up
# ---------------------------------------------------------------------------

def sent_today(instance):
    return frappe.db.count(
        "WhatsApp Message",
        {"instance": instance, "status": "Sent", "creation": [">=", nowdate()]},
    )


def instance_age_days(instance):
    created = frappe.db.get_value("WhatsApp Instance", instance, "creation")
    if not created:
        return None
    if isinstance(created, str):
        created = datetime.fromisoformat(created)
    return (now_datetime() - created).days


def effective_daily_limit(instance):
    """Configured cap, tightened by the warm-up ramp for young instances.

    Returns 0 for "unlimited".
    """
    conf = get_conf()
    limit = int(conf.daily_message_limit or 0)

    if conf.enable_warmup:
        age = instance_age_days(instance)
        if age is not None:
            for max_age, warmup_limit in WARMUP_SCHEDULE:
                if age < max_age:
                    limit = min(limit, warmup_limit) if limit else warmup_limit
                    break
    return limit


def can_send(instance):
    """(allowed, reason) - whether this instance may send one more message today."""
    if not enabled():
        return True, ""
    limit = effective_daily_limit(instance)
    if not limit:
        return True, ""
    sent = sent_today(instance)
    if sent >= limit:
        return False, (
            f"Daily limit reached for instance {instance} ({sent}/{limit} sent today)"
        )
    return True, ""


# ---------------------------------------------------------------------------
# Number verification
# ---------------------------------------------------------------------------

def number_exists(instance, phone):
    """True if ``phone`` is registered on WhatsApp (fail-open on any doubt)."""
    conf = get_conf()
    if not conf.enable_anti_ban or not conf.verify_numbers:
        return True
    if not phone or "@" in phone:  # group/broadcast JIDs can't be user-checked
        return True

    cache_key = f"wa_number_check:{phone}"
    cached = frappe.cache.get_value(cache_key)
    if cached is not None:
        return cached == "1"

    try:
        token = wuzapi.instance_token(instance)
        if not token:
            return True
        data = wuzapi.check_users(token, [phone])
        users = (data.get("data") or {}).get("Users") or []
        if len(users) != 1:
            return True  # unexpected shape - don't block the send
        on_whatsapp = bool(users[0].get("IsInWhatsapp", users[0].get("isInWhatsapp")))
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"WhatsApp number check failed for {phone}",
        )
        return True

    frappe.cache.set_value(
        cache_key, "1" if on_whatsapp else "0", expires_in_sec=NUMBER_CACHE_TTL
    )
    return on_whatsapp


# ---------------------------------------------------------------------------
# Queue drain (scheduled)
# ---------------------------------------------------------------------------

def flush_queued_messages():
    """Send messages parked as Queued, oldest first, respecting per-instance caps.

    Runs from scheduler_events (see hooks.py). Instances still at their cap
    keep their backlog; other instances continue to drain.
    """
    if sending_paused():
        return
    names = frappe.get_all(
        "WhatsApp Message",
        filters={"status": "Queued"},
        order_by="creation asc",
        pluck="name",
        limit=QUEUE_DRAIN_BATCH,
    )
    capped_instances = set()
    for name in names:
        doc = frappe.get_doc("WhatsApp Message", name)
        if doc.instance in capped_instances:
            continue
        allowed, _reason = can_send(doc.instance)
        if not allowed:
            capped_instances.add(doc.instance)
            continue
        doc.dispatch()
        frappe.db.commit()
        pause_between_sends()
