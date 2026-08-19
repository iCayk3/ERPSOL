app_name = "sol_brasil"
app_title = "SOL Brasil"
app_publisher = "SOL NOC"
app_description = "Localizacao brasileira e personalizacoes da SOL"
app_email = "desenvolvimento@sol.local"
app_license = "gpl-3.0"

app_logo_url = "/assets/sol_brasil/images/sol-provedor-logo.svg"
app_home = "/desk/sol-provedor"
app_include_js = [
	"/assets/sol_brasil/js/customer_quick_entry.js",
	"/assets/sol_brasil/js/related_return.js",
]

# Apps
# ------------------

required_apps = ["erpnext"]

add_to_apps_screen = [
	{
		"name": "sol_brasil",
		"logo": app_logo_url,
		"title": "SOL Provedor",
		"route": app_home,
	}
]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "sol_brasil",
# 		"logo": "/assets/sol_brasil/logo.png",
# 		"title": "SOL Brasil",
# 		"route": "/sol_brasil",
# 		"has_permission": "sol_brasil.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sol_brasil/css/sol_brasil.css"
# app_include_js = "/assets/sol_brasil/js/sol_brasil.js"

# include js, css files in header of web template
# web_include_css = "/assets/sol_brasil/css/sol_brasil.css"
# web_include_js = "/assets/sol_brasil/js/sol_brasil.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sol_brasil/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Customer": "public/js/customer.js",
	"Sales Invoice": "public/js/sales_invoice.js",
	"Issue": "public/js/issue.js",
	"Maintenance Visit": "public/js/maintenance_visit.js",
	"Lead": "public/js/lead.js",
	"Contrato Preliminar": "public/js/contrato_preliminar.js",
	"Subscription": "public/js/subscription.js",
	"Address": "public/js/address_contact.js",
	"Contact": "public/js/address_contact.js",
}
doctype_list_js = {"Customer": "public/js/customer_list.js"}
override_doctype_dashboards = {"Customer": "sol_brasil.customer_dashboard.get_dashboard_data"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "sol_brasil/public/icons.svg"

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

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "sol_brasil.utils.jinja_methods",
# 	"filters": "sol_brasil.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sol_brasil.install.before_install"
after_install = "sol_brasil.install.after_install"
after_migrate = ["sol_brasil.install.after_migrate"]

# Uninstallation
# ------------

# before_uninstall = "sol_brasil.uninstall.before_uninstall"
# after_uninstall = "sol_brasil.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "sol_brasil.utils.before_app_install"
# after_app_install = "sol_brasil.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "sol_brasil.utils.before_app_uninstall"
# after_app_uninstall = "sol_brasil.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "sol_brasil.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sol_brasil.notifications.get_notification_config"

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

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Customer": {
		"validate": "sol_brasil.customer.validate_customer",
		"after_insert": "sol_brasil.lead.finalize_lead_conversion",
	},
	"Lead": {"validate": "sol_brasil.customer.validate_lead"},
	"Issue": {
		"validate": "sol_brasil.service.validate_issue_subject",
		"after_insert": "sol_brasil.service.register_issue_creation",
		"on_update": "sol_brasil.service.register_issue_update",
	},
	"Maintenance Visit": {
		"validate": "sol_brasil.service.validate_service_order_links",
		"before_submit": "sol_brasil.service.validate_service_order_completion",
		"after_insert": "sol_brasil.service.create_or_link_issue_for_service_order",
	},
	"Subscription": {
		"validate": "sol_brasil.subscription.validate_installation_address",
		"after_insert": "sol_brasil.subscription.register_contract_creation",
		"on_update": "sol_brasil.subscription.register_contract_update",
		"on_trash": "sol_brasil.subscription.register_contract_deletion",
	},
	"Sales Invoice": {
		"validate": "sol_brasil.subscription.validate_invoice_contract",
		"after_insert": "sol_brasil.financial_activity.register_invoice_creation",
		"on_update": "sol_brasil.financial_activity.register_invoice_update",
		"on_submit": "sol_brasil.financial_activity.register_invoice_submit",
		"on_cancel": "sol_brasil.financial_activity.register_invoice_cancel",
		"on_trash": "sol_brasil.financial_activity.register_invoice_deletion",
	},
	"Payment Entry": {
		"after_insert": "sol_brasil.financial_activity.register_payment_creation",
		"on_submit": "sol_brasil.financial_activity.register_payment_submit",
		"on_cancel": "sol_brasil.financial_activity.register_payment_cancel",
		"on_trash": "sol_brasil.financial_activity.register_payment_deletion",
	},
	"Address": {"on_update": "sol_brasil.customer.notify_linked_customer_update"},
	"Contact": {"on_update": "sol_brasil.customer.notify_linked_customer_update"},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"sol_brasil.tasks.all"
# 	],
# 	"daily": [
# 		"sol_brasil.tasks.daily"
# 	],
# 	"hourly": [
# 		"sol_brasil.tasks.hourly"
# 	],
# 	"weekly": [
# 		"sol_brasil.tasks.weekly"
# 	],
# 	"monthly": [
# 		"sol_brasil.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "sol_brasil.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "sol_brasil.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "sol_brasil.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sol_brasil.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["sol_brasil.utils.before_request"]
# after_request = ["sol_brasil.utils.after_request"]

# Job Events
# ----------
# before_job = ["sol_brasil.utils.before_job"]
# after_job = ["sol_brasil.utils.after_job"]

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
# 	"sol_brasil.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
