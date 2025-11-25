from pywa import WhatsApp, errors
import frappe

@frappe.whitelist()
def setup():
    wa = WhatsApp(
        phone_id="281222978402210",  # Replace with actual phone_id
        token="EAAlXQfMg4WYBOwXInAXRL6DRosO4cYhW8EupZAkel5bxJPbZAnMipygBWTzZAfx9KRPEZBgdZCIvObMOoeaZBuCo24t1TMNo1fGZCjnuQ53OxE9NshZC4UoZCfb4zFwuYLtYJQOB3k10duBtZCszTWW3NcPiaW8yUL97WizKDSAqUmRJLpLcausksZBBARtIQ2XCk6j",
        business_account_id ="238439702693470"    
    )
    return wa