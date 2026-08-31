import json

import frappe


MODULES = {
    "SOL Provedor": {
        "label": "SOL Provedor",
        "icon": "home",
        "shortcuts": [
            ("Clientes", "/app/clientes"),
            ("Contratos", "/app/contratos"),
            ("Planos", "/app/planos"),
            ("Financeiro", "/app/financeiro"),
            ("Atendimento", "/app/atendimento"),
            ("Rede e equipamentos", "/app/rede-e-equipamentos"),
            ("Estoque", "/app/estoque"),
            ("Relatórios", "/app/relatórios"),
            ("Configurações", "/app/configurações"),
        ],
    },
    "Contratos": {
        "icon": "file-text",
        "shortcuts": [
            ("Listagem de contratos", "Subscription", "List"),
            ("Novo contrato", "Subscription", "New"),
        ],
    },
    "Planos": {
        "icon": "package",
        "shortcuts": [
            ("Planos de internet", "Subscription Plan", "List"),
            ("Cadastrar plano", "Subscription Plan", "New"),
            ("Serviços e produtos", "Item", "List"),
        ],
    },
    "Financeiro": {
        "icon": "credit-card",
        "shortcuts": [
            ("Central de cobrança", "central-de-cobranca", "Page"),
            ("Faturas", "Sales Invoice", "List"),
            ("Emitir fatura", "Sales Invoice", "New"),
            ("Recebimentos", "Payment Entry", "List"),
            ("Registrar recebimento", "Payment Entry", "New"),
            ("Cobranças", "Dunning", "List"),
        ],
    },
    "Atendimento": {
        "icon": "headphones",
        "shortcuts": [
            ("Atendimentos", "Issue", "List"),
            ("Novo atendimento", "Issue", "New"),
            ("Assuntos de atendimento", "Assunto de Atendimento", "List"),
            ("Serviços do provedor", "Servico do Provedor", "List"),
            ("Garantias", "Warranty Claim", "List"),
        ],
    },
    "Rede e Equipamentos": {
        "route": "rede-e-equipamentos",
        "icon": "server",
        "shortcuts": [
			("Servidores NAS", "NAS RADIUS", "List"),
            ("OLTs", "OLT", "List"),
			("Caixas CTO/NAP", "Caixa de Atendimento", "List"),
            ("Fabricantes", "Brand", "List"),
            ("Modelos e itens", "Item", "List"),
            ("Equipamentos", "Asset", "List"),
            ("Cadastrar equipamento", "Asset", "New"),
            ("Números de série", "Serial No", "List"),
            ("Locais de instalação", "Location", "List"),
        ],
    },
    "Estoque": {
        "icon": "archive",
        "shortcuts": [
            ("Itens", "Item", "List"),
            ("Movimentações", "Stock Entry", "List"),
            ("Nova movimentação", "Stock Entry", "New"),
            ("Depósitos", "Warehouse", "List"),
        ],
    },
    "Relatórios": {
        "icon": "bar-chart-2",
        "shortcuts": [
            ("Contas a receber", "Accounts Receivable", "Report"),
            ("Razão contábil", "General Ledger", "Report"),
            ("Saldo de estoque", "Stock Balance", "Report"),
        ],
    },
    "Configurações": {
        "icon": "settings",
        "shortcuts": [
			("Regras de negócio", "Regras de Negocio", "List"),
			("Configurações do provedor", "Configurações do Provedor", "List"),
			("Integração FiberHome UNM", "Configurações FiberHome UNM", "List"),
            ("Empresa", "Company", "List"),
            ("Usuários", "User", "List"),
			("Permissões", "/app/permission-manager"),
            ("Configurações do sistema", "System Settings", "List"),
        ],
    },
	"Regras de negócio": {
		"route": "regras-de-negocio",
		"icon": "sliders",
		"shortcuts": [
			("Configurar regras dos contratos", "Regras de Negocio", "List"),
		],
	},
}


HIDDEN_STANDARD_WORKSPACES = (
    "Assets",
    "Build",
    "Buying",
    "CRM",
    "ERPNext Settings",
    "Financial Reports",
    "Integrations",
    "Invoicing",
    "Manufacturing",
    "Projects",
    "Quality",
    "Selling",
    "Stock",
    "Subcontracting",
    "Support",
    "Users",
    "Website",
    "Welcome Workspace",
)

HIDDEN_STANDARD_DESKTOP_ICONS = (
    "Framework",
    "Organization",
    "Accounting",
    "Assets",
    "Buying",
    "Manufacturing",
    "Projects",
    "Quality",
    "Selling",
    "Stock",
    "Subcontracting",
    "ERPNext Settings",
    "Assinantes",
    "Contratos",
    "Planos",
)

DESKTOP_GROUPS = {
    "Operação": {
        "icon": "activity",
        "idx": 3,
        "items": ("Atendimento", "Rede e Equipamentos", "Estoque"),
    },
    "Gestão": {
        "icon": "briefcase",
        "idx": 4,
        "items": ("Financeiro", "Relatórios", "Configurações"),
    },
    "Configurações do Sistema": {
        "icon": "settings",
        "bg_color": "gray",
        "idx": 5,
        "items": (
            "Automation",
            "Build",
            "Data",
            "Email",
            "Integrations",
            "Printing",
            "System",
			"Regras de negócio",
            "Users",
            "Website",
        ),
    },
}


def sync_provider_workspaces():
    _sync_customer_workspace()
    for name, definition in MODULES.items():
        _sync_workspace(name, definition)

    _sync_desktop_icons()

    for name in HIDDEN_STANDARD_WORKSPACES:
        if frappe.db.exists("Workspace", name):
            frappe.db.set_value("Workspace", name, "is_hidden", 1, update_modified=False)

    frappe.clear_cache()


def _sync_customer_workspace():
	if not frappe.db.exists("Workspace", "Clientes"):
		return
	workspace = frappe.get_doc("Workspace", "Clientes")
	shortcuts = [
		("Listagem de clientes", "Customer", "List"),
		("Futuros clientes (Leads)", "Lead", "List"),
	]
	workspace.content = _content(shortcuts, "Clientes")
	workspace.set("shortcuts", [])
	for label, doctype, view in shortcuts:
		workspace.append(
			"shortcuts",
			{"label": label, "type": "DocType", "link_to": doctype, "doc_view": view},
		)
	workspace.save(ignore_permissions=True)


def _sync_desktop_icons():
    from frappe.desk.doctype.desktop_icon.desktop_icon import (
        add_workspace_to_desktop,
        clear_desktop_icons_cache,
    )

    for index, (name, definition) in enumerate(MODULES.items(), start=1):
        add_workspace_to_desktop(name)
        desktop_index = index if name == "SOL Provedor" else index + 1
        frappe.db.set_value(
            "Desktop Icon",
            name,
            {
                "idx": desktop_index,
                "icon": definition["icon"],
                "bg_color": "blue",
                "hidden": 0,
                "parent_icon": None,
            },
            update_modified=False,
        )

    # Clientes já existia antes do painel principal e também deve ficar na grade.
    add_workspace_to_desktop("Clientes")
    frappe.db.set_value(
        "Desktop Icon",
        "Clientes",
        {
            "idx": 2,
            "icon": "users",
            "bg_color": "blue",
            "hidden": 0,
            "parent_icon": None,
        },
        update_modified=False,
    )

    for group_name, group in DESKTOP_GROUPS.items():
        if frappe.db.exists("Desktop Icon", group_name):
            folder = frappe.get_doc("Desktop Icon", group_name)
        else:
            folder = frappe.new_doc("Desktop Icon")
            folder.label = group_name

        folder.update(
            {
                "icon_type": "Folder",
                "link_type": "Workspace Sidebar",
                "idx": group["idx"],
                "icon": group["icon"],
                "bg_color": group.get("bg_color", "blue"),
                "hidden": 0,
                "standard": 0,
                "parent_icon": None,
            }
        )
        folder.save(ignore_permissions=True)

        for item_index, item_name in enumerate(group["items"], start=1):
            frappe.db.set_value(
                "Desktop Icon",
                item_name,
                {"parent_icon": group_name, "idx": item_index, "hidden": 0},
                update_modified=False,
            )

    frappe.db.set_value(
        "Desktop Icon",
        "SOL Provedor",
        {"parent_icon": None, "idx": 1, "hidden": 0},
        update_modified=False,
    )

    frappe.db.set_value(
        "Desktop Icon",
        "Clientes",
        {"parent_icon": None, "idx": 2, "hidden": 0},
        update_modified=False,
    )

    for name in HIDDEN_STANDARD_DESKTOP_ICONS:
        if frappe.db.exists("Desktop Icon", name):
            frappe.db.set_value("Desktop Icon", name, "hidden", 1, update_modified=False)

    clear_desktop_icons_cache("Administrator")


def _sync_workspace(name, definition):
    if frappe.db.exists("Workspace", name):
        workspace = frappe.get_doc("Workspace", name)
        if workspace.app not in (None, "", "sol_brasil"):
            return
    else:
        workspace = frappe.new_doc("Workspace")
        workspace.name = name

    label = definition.get("label", name)
    shortcuts = definition["shortcuts"]
    workspace.update(
        {
            "label": label,
            "title": label,
            "module": "SOL Brasil",
            "app": "sol_brasil",
            "type": "Workspace",
            "icon": definition["icon"],
            "public": 1,
            "is_hidden": 0,
            "sequence_id": 1 if name == "SOL Provedor" else 2,
            "content": _content(shortcuts, label),
        }
    )
    workspace.set("shortcuts", [])
    for shortcut in shortcuts:
        if len(shortcut) == 2:
            workspace.append(
                "shortcuts",
                {"label": shortcut[0], "type": "URL", "url": shortcut[1]},
            )
        elif shortcut[2] in ("Report", "Page"):
            workspace.append(
                "shortcuts",
                {"label": shortcut[0], "type": shortcut[2], "link_to": shortcut[1]},
            )
        else:
            workspace.append(
                "shortcuts",
                {
                    "label": shortcut[0],
                    "type": "DocType",
                    "link_to": shortcut[1],
                    "doc_view": shortcut[2],
                },
            )

    workspace.flags.ignore_links = True
    workspace.save(ignore_permissions=True)


def _content(shortcuts, title):
    blocks = [
        {
            "id": f"sol-{frappe.scrub(title)}-header",
            "type": "header",
            "data": {"text": f'<span class="h4"><b>{title}</b></span>', "col": 12},
        }
    ]
    for index, shortcut in enumerate(shortcuts, start=1):
        blocks.append(
            {
                "id": f"sol-{frappe.scrub(title)}-{index}",
                "type": "shortcut",
                "data": {"shortcut_name": shortcut[0], "col": 4},
            }
        )
    return json.dumps(blocks, ensure_ascii=False, separators=(",", ":"))
