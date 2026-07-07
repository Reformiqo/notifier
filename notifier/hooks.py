app_name = "notifier"
app_title = "Notifier"
app_publisher = "royalsmb"
app_description = "Frappe notifier"
app_email = "info@royalsmb.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "notifier",
# 		"logo": "/assets/notifier/logo.png",
# 		"title": "Notifier",
# 		"route": "/notifier",
# 		"has_permission": "notifier.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/notifier/css/notifier.css"
# app_include_js = "/assets/notifier/js/notifier.js"

# include js, css files in header of web template
# web_include_css = "/assets/notifier/css/notifier.css"
# web_include_js = "/assets/notifier/js/notifier.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "notifier/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "notifier/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "notifier.utils.jinja_methods",
# 	"filters": "notifier.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "notifier.install.before_install"
# after_install = "notifier.install.after_install"

# Set up the WhatsApp Notification channel on both fresh installs and upgrades
# (patches are skipped on a fresh install, so a hook is required here).
after_install = "notifier.setup.setup_notification_channel"
after_migrate = "notifier.setup.setup_notification_channel"

# Uninstallation
# ------------

# before_uninstall = "notifier.uninstall.before_uninstall"
# after_uninstall = "notifier.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "notifier.utils.before_app_install"
# after_app_install = "notifier.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "notifier.utils.before_app_uninstall"
# after_app_uninstall = "notifier.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "notifier.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	# Adds a "WhatsApp" channel to the standard Notification doctype.
	"Notification": "notifier.overrides.notification.WhatsAppNotification",
}

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
	
    


# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron": {
		# Keep WhatsApp Instance status in sync with WuzAPI. Webhooks may be
		# unreachable (e.g. site behind localhost), so we also poll every 2 min.
		"*/2 * * * *": ["notifier.api.check_instance_status"],
	}
}

# scheduler_events = {
	
# 	"daily": [
# 		"notifier.tasks.daily"
# 	],
# 	"hourly": [
# 		"notifier.tasks.hourly"
# 	],
# 	"weekly": [
# 		"notifier.tasks.weekly"
# 	],
# 	"monthly": [
# 		"notifier.tasks.monthly"
# 	],
    
# }

# Testing
# -------

# before_tests = "notifier.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "notifier.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "notifier.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["notifier.utils.before_request"]
# after_request = ["notifier.utils.after_request"]

# Job Events
# ----------
# before_job = ["notifier.utils.before_job"]
# after_job = ["notifier.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"notifier.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


fixtures = [
    {"doctype": "Client Script", 
    "filters": [["module" , "in" , ("Notifier")]]
    },
    {"doctype": "Custom Field",
    "filters": [["module" , "in" , ("Notifier")]]
    },
  
    ]