// Copyright (c) 2025, royalsmb and contributors
// For license information, please see license.txt

    // frappe.ui.form.on("WhatsApp Message", {
    // 	refresh(frm) {

// 	},
// });

// Source - https://stackoverflow.com/a
// Posted by esafwan
// Retrieved 2025-12-02, License - CC BY-SA 4.0

frappe.ui.form.on('WhatsApp Message', {
    file_attachment: function(frm) {       
        frm.set_value('skip_notification', true);
        frm.save_or_update(); 
    },
    after_save: function(frm) {       
        frm.set_value('skip_notification', false);
    }
});
