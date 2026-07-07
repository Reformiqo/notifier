// Copyright (c) 2025, royalsmb and contributors
// For license information, please see license.txt

// Sending happens server-side (WhatsAppMessage.after_insert -> WuzAPI).
frappe.ui.form.on("WhatsApp Message", {
	setup(frm) {
		// Only offer groups that belong to the selected instance.
		frm.set_query("group", function () {
			return { filters: { instance: frm.doc.instance } };
		});
	},
});
