// Copyright (c) 2025, royalsmb and contributors
// For license information, please see license.txt

frappe.ui.form.on("WhatsApp Instance", {
	refresh(frm) {
		if (frm.is_new()) return;

		// Regenerate + scan the QR code (only while not yet connected).
		if (frm.doc.status !== "Open") {
			frm.add_custom_button(__("Refresh QR Code"), function () {
				frm.call({
					method: "connect_instance",
					args: { instance: frm.doc.name },
					freeze: true,
					freeze_message: __("Generating QR code..."),
					callback: function () {
						frm.save("Update", function () {
							window.location.reload();
						});
					},
				});
			});
		}

		// Pull live connection state from WuzAPI and, if connected, sync groups.
		frm.add_custom_button(__("Check Connection"), function () {
			frm.call({
				method: "check_connection",
				args: { instance: frm.doc.name },
				freeze: true,
				freeze_message: __("Checking connection & syncing groups..."),
				callback: function (r) {
					const g = r.message && r.message.groups;
					if (g) {
						frappe.show_alert({
							message: __("Synced {0} groups ({1} new)", [g.fetched, g.new]),
							indicator: "green",
						});
					}
					frm.reload_doc();
				},
			});
		});

		// Auto-reconcile once when the form opens and it isn't Open yet, so the
		// badge flips to "Open" after a scan without waiting for the scheduler.
		if (frm.doc.status !== "Open" && !frm.__wa_checked) {
			frm.__wa_checked = true;
			frm.call({
				method: "get_instance_status",
				args: { instance: frm.doc.name },
			}).then(function () {
				if (frm.doc.status !== "Open") frm.reload_doc();
			});
		}
	},
});
