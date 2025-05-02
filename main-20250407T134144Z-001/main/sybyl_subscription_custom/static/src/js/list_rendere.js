/** @odoo-module */

import { ListRenderer } from "@web/views/list/list_renderer";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(ListRenderer.prototype, {
	getGroupDisplayName(group) {
        if (group.groupByField.name === "check_in_out_state" && !group.value) {
            return _t("Checked In");
        } else if (group.groupByField.name === "check_in_out_state" && group.value) {
            return _t("Checked Out");
        } else {
            return super.getGroupDisplayName(group);
        }
    }
});