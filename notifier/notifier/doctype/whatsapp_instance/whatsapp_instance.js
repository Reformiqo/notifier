// Copyright (c) 2025, royalsmb and contributors
// For license information, please see license.txt

frappe.ui.form.on("WhatsApp Instance", {
	refresh(frm) {
        // add a custom button to the form
        // if status is not open 
        if (frm.doc.status !== "Open") {
    frm.add_custom_button("Refresh QR Code", function() {
            // freeze the page  for 10 seconds and then refresh the page

            frm.call({
                method: "connect_instance",
                args: { instance: frm.doc.name },
                freeze: true,
                callback: function(r) {
                    console.log(r);
                    // frm.set_value("qr_code", r.file_url);
                    
                    // Save the form first before reloading
                    frm.save('Update', function() {
                        // Only reload after successful save
                        window.location.reload();
                    });
                }
            });
        });
        }

	},
});
