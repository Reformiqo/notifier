"""Rename the old "Evolution API Settings" single doctype to "WhatsApp Settings".

Runs in pre_model_sync so the existing DB record (and its stored base_url /
api_token values) is renamed *before* model sync recreates the doctype from the
new JSON. On a fresh install the old doctype does not exist, so this is a no-op.
"""

import frappe

OLD = "Evolution API Settings"
NEW = "WhatsApp Settings"


def execute():
    if frappe.db.exists("DocType", OLD) and not frappe.db.exists("DocType", NEW):
        frappe.rename_doc(
            "DocType", OLD, NEW, force=True, ignore_permissions=True
        )
        frappe.clear_cache(doctype=NEW)
