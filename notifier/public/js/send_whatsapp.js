// "Actions > Send WhatsApp" in list and form views.
//
// Select one or more documents (e.g. Sales Invoices) -> Actions -> Send WhatsApp
// -> choose the WhatsApp Instance and Print Format -> Send. Each document's PDF
// is sent to its customer's / supplier's number through that instance (WuzAPI).
// Nothing opens in the browser and no WhatsApp Web login is needed.
(() => {
	const LABEL = __("Send WhatsApp");
	const PARTY_FIELDS = ["customer", "supplier", "party", "party_name", "contact_mobile"];
	const LAST_KEY = "notifier_whatsapp_last";

	// Only party documents that can be printed (invoices, orders, quotations...).
	function is_supported(doctype) {
		if (!doctype || !frappe.model.can_print(doctype)) return false;
		const meta = frappe.get_meta(doctype);
		if (!meta || meta.issingle || meta.istable) return false;
		return PARTY_FIELDS.some((f) => frappe.meta.has_field(doctype, f));
	}

	function load_last() {
		try {
			return JSON.parse(localStorage.getItem(LAST_KEY)) || {};
		} catch (e) {
			return {};
		}
	}

	function save_last(values) {
		try {
			localStorage.setItem(
				LAST_KEY,
				JSON.stringify({ instance: values.instance, ["pf:" + values.doctype]: values.print_format })
			);
		} catch (e) {
			// ignore
		}
	}

	function show_result(r) {
		if (!r) return;
		if (r.queued) {
			frappe.show_alert({
				message: __("Sending {0} documents on WhatsApp in the background...", [r.count]),
				indicator: "blue",
			});
			return;
		}
		const sent = r.sent || [];
		const failed = r.failed || [];
		if (!failed.length) {
			frappe.show_alert({
				message: __("Sent {0} PDF(s) on WhatsApp", [sent.length]),
				indicator: "green",
			});
			return;
		}
		const rows = failed
			.map((f) => `<li><b>${frappe.utils.escape_html(f.name)}</b>: ${frappe.utils.escape_html(f.error)}</li>`)
			.join("");
		frappe.msgprint({
			title: __("WhatsApp: {0} sent, {1} failed", [sent.length, failed.length]),
			message: `<ul>${rows}</ul>`,
			indicator: sent.length ? "orange" : "red",
		});
	}

	// Result of a background (bulk) send.
	$(document).on("app_ready", () => frappe.realtime.on("notifier_whatsapp_sent", show_result));

	function open_dialog(doctype, names, after_send) {
		if (!names.length) {
			frappe.msgprint(__("Please select at least one document."));
			return;
		}
		frappe
			.xcall("notifier.send.get_dialog_defaults", { doctype, names })
			.then((defaults) => {
				const last = load_last();
				const single = names.length === 1;
				const phones = defaults.phones || {};
				const missing = names.filter((n) => !phones[n]);

				let summary = "";
				if (!single) {
					summary = `<p>${__("{0} documents selected. Each PDF goes to that document's own customer number.", [names.length])}</p>`;
					if (missing.length) {
						summary += `<p class="text-danger">${__("No phone number found for: {0}", [
							missing.map(frappe.utils.escape_html).join(", "),
						])}</p>`;
					}
				}

				const d = new frappe.ui.Dialog({
					title: LABEL,
					fields: [
						{
							fieldname: "instance",
							fieldtype: "Link",
							label: __("WhatsApp Instance"),
							options: "WhatsApp Instance",
							reqd: 1,
							default: last.instance || defaults.instance,
							get_query: () => ({ filters: { status: "Open" } }),
						},
						{
							fieldname: "print_format",
							fieldtype: "Link",
							label: __("Print Format"),
							options: "Print Format",
							default: last["pf:" + doctype] || defaults.print_format,
							description: __("Leave empty for Standard."),
							get_query: () => ({ filters: { doc_type: doctype, disabled: 0 } }),
						},
						{
							fieldname: "no_letterhead",
							fieldtype: "Check",
							label: __("Without Letter Head"),
						},
						{ fieldtype: "Column Break" },
						{
							fieldname: "phone",
							fieldtype: "Data",
							label: __("Customer WhatsApp Number"),
							description: __("With country code; 10-digit numbers get the default country code."),
							default: single ? phones[names[0]] : "",
							reqd: single ? 1 : 0,
							hidden: single ? 0 : 1,
						},
						{
							fieldname: "message",
							fieldtype: "Small Text",
							label: __("Message (sent before the PDF)"),
							default: defaults.message,
							description: __("Optional. Jinja allowed, e.g. {{ doc.name }}."),
						},
						{ fieldtype: "Section Break" },
						{ fieldname: "summary", fieldtype: "HTML", options: summary },
					],
					size: "large",
					primary_action_label: __("Send"),
					primary_action(values) {
						save_last({ ...values, doctype });
						d.hide();
						frappe
							.xcall(
								"notifier.send.send_documents",
								{
									doctype,
									names,
									instance: values.instance,
									print_format: values.print_format || null,
									message: values.message || "",
									phone: single ? values.phone : null,
									no_letterhead: values.no_letterhead ? 1 : 0,
								},
								null,
								{ freeze: true, freeze_message: __("Sending on WhatsApp...") }
							)
							.then((r) => {
								show_result(r);
								after_send && after_send(r);
							});
					},
				});
				d.show();
			});
	}

	// --- List view: Actions menu (works on the checked rows) ---------------
	const ListView = frappe.views && frappe.views.ListView;
	if (ListView && !ListView.prototype.__notifier_whatsapp) {
		ListView.prototype.__notifier_whatsapp = true;
		const original = ListView.prototype.get_actions_menu_items;
		ListView.prototype.get_actions_menu_items = function () {
			const items = original.call(this);
			if (is_supported(this.doctype)) {
				items.push({
					label: LABEL,
					action: () =>
						open_dialog(this.doctype, this.get_checked_items(true), () => this.refresh()),
					standard: true,
				});
			}
			return items;
		};
	}

	// --- Form view: Actions > Send WhatsApp ---------------------------------
	$(document).on("form-refresh", (e, frm) => {
		if (!frm || frm.is_new() || frm.doc.docstatus === 2 || !is_supported(frm.doctype)) return;
		// After the form's own refresh handlers (incl. site Client Scripts), so this
		// replaces any older "Send WhatsApp" button that opened WhatsApp Web.
		setTimeout(() => {
			frm.remove_custom_button(LABEL, __("Actions"));
			frm.add_custom_button(
				LABEL,
				() => open_dialog(frm.doctype, [frm.docname], () => frm.reload_doc()),
				__("Actions")
			);
		}, 300);
	});
})();
