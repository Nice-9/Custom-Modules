/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { PivotModel } from "@web/views/pivot/pivot_model";
import { patch } from "@web/core/utils/patch";
console.log('___ PivotModel : ', PivotModel);
patch(PivotModel.prototype, {
    /**
     * Extract from a groupBy value a label.
     *
     * @protected
     * @param {any} value
     * @param {string} groupBy
     * @param {Config} config
     * @returns {string}
     */
    _sanitizeLabel(value, groupBy, config) {
        const { metaData } = config;
        const fieldName = groupBy.split(":")[0];
        if (
            fieldName &&
            metaData.fields[fieldName] &&
            metaData.fields[fieldName].type === "boolean"
        ) {
            if( fieldName == 'check_in_out_state'){
                return value === undefined ? _t("None") : value ? _t("Checked Out") : _t("Checked In");
            }
            return super._sanitizeLabel(value, groupBy, config);
        }
        return super._sanitizeLabel(value, groupBy, config);
        
    }
});