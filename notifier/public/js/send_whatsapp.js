// "Actions > Send WhatsApp" on every doctype that has an enabled Notification
// with channel "WhatsApp". Sends through the WhatsApp Instance (WuzAPI) with the
// Notification's message and print-format PDF; no WhatsApp Web tab is opened.
(() => {
	const LABEL = __("Send WhatsApp");
	const GROUP = __("Actions");

	function send_whatsapp(frm) {
		frappe
			.xcall("notifier.send.get_send_options", { doctype: frm.doctype, name: frm.docname })
			.then((options) => {
				if (!options || !options.length) {
					frappe.msgprint(__("No enabled WhatsApp Notification for {0}.", [__(frm.doctype)]));
					return;
				}
				const by_name = Object.fromEntries(options.map((o) => [o.name, o]));
				const first = options[0];

				const describe = (o) =>
					o.attach_print
						? __("The message and the PDF ({0}) will be sent from the WhatsApp Instance.", [
								o.print_format || __("Standard"),
						  ])
						: __("The message will be sent from the WhatsApp Instance.");

				const d = new frappe.ui.Dialog({
					title: LABEL,
					fields: [
						{
							fieldname: "notification",
							fieldtype: "Select",
							label: __("Notification"),
							options: options.map((o) => o.name),
							default: first.name,
							reqd: 1,
							hidden: options.length === 1,
							onchange() {
								const o = by_name[d.get_value("notification")];
								if (!o) return;
								d.set_value("phone", o.phone || "");
								d.set_df_property("phone", "hidden", o.send_to === "Group");
								d.set_df_property("group", "hidden", o.send_to !== "Group");
								d.set_value("group", o.group || "");
								d.set_df_property("info", "options", `<p class="text-muted">${describe(o)}</p>`);
							},
						},
						{
							fieldname: "phone",
							fieldtype: "Data",
							label: __("Phone Number(s)"),
							description: __("With country code; separate several numbers with commas."),
							default: first.phone,
							hidden: first.send_to === "Group",
						},
						{
							fieldname: "group",
							fieldtype: "Data",
							label: __("WhatsApp Group"),
							read_only: 1,
							default: first.group,
							hidden: first.send_to !== "Group",
						},
						{
							fieldname: "info",
							fieldtype: "HTML",
							options: `<p class="text-muted">${describe(first)}</p>`,
						},
					],
					primary_action_label: __("Send"),
					primary_action(values) {
						d.get_primary_btn().prop("disabled", true);
						frappe
							.xcall(
								"notifier.send.send_document",
								{
									doctype: frm.doctype,
									name: frm.docname,
									notification: values.notification,
									phone: values.phone,
								},
								null,
								{ freeze: true, freeze_message: __("Sending on WhatsApp...") }
							)
							.then((r) => {
								d.hide();
								frappe.show_alert({
									message: __("Sent on WhatsApp to {0}", [(r.targets || []).join(", ")]),
									indicator: "green",
								});
								frm.reload_doc();
							})
							.finally(() => d.get_primary_btn().prop("disabled", false));
					},
				});
				d.show();
			});
	}

	function add_button(frm) {
		const doctypes = frappe.boot.notifier_whatsapp_doctypes || [];
		if (frm.is_new() || !doctypes.includes(frm.doctype)) return;
		// Run after the form's own refresh handlers (incl. site Client Scripts),
		// replacing any older "Send WhatsApp" button that opened WhatsApp Web.
		setTimeout(() => {
			frm.remove_custom_button(LABEL, GROUP);
			frm.add_custom_button(LABEL, () => send_whatsapp(frm), GROUP);
		}, 300);
	}

	$(document).on("form-refresh", (e, frm) => frm && add_button(frm));
})();
