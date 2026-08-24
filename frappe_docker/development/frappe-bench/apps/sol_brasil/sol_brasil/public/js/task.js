function sol_update_dependency_checklist(frm) {
	const grid = frm.fields_dict.depends_on?.grid;
	if (!grid) return;
	grid.update_docfield_property("custom_completed", "in_list_view", 1);
}

frappe.ui.form.on("Task", {
	refresh(frm) {
		sol_update_dependency_checklist(frm);
		frm.set_df_property(
			"depends_on",
			"description",
			__("Use como checklist. Marque Concluído e salve para finalizar a tarefa vinculada.")
		);
	},
});

frappe.ui.form.on("Task Depends On", {
	custom_open_task(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.task) frappe.set_route("Form", "Task", row.task);
	},
});
