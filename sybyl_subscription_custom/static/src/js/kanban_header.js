/** @odoo-module */

import { KanbanHeader } from "@web/views/kanban/kanban_header";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { isRelational } from "@web/model/relational_model/utils";
import { isNull } from "@web/views/utils";

patch(KanbanHeader.prototype, {
	get groupName() {
        const { groupByField, displayName } = this.group;
        let name = displayName;
        if (groupByField.type === "boolean") {
        	if (groupByField.name == "check_in_out_state"){
        		name = name ? _t("Checked Out") : _t("Checked In");
        	}else{

            name = name ? _t("Yes") : _t("No");
        	}
        } else if (!name) {
            if (
                isRelational(groupByField) ||
                groupByField.type === "date" ||
                groupByField.type === "datetime" ||
                isNull(name)
            ) {
                name = this._getEmptyGroupLabel(groupByField.name);
            }
        }
        return name;
    }
});