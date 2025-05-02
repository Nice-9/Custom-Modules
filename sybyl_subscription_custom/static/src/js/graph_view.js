/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { GraphModel } from "@web/views/graph/graph_model";
import { patch } from "@web/core/utils/patch";

patch(GraphModel.prototype, {
	/**
     * Fetch and process graph data.  It is basically a(some) read_group(s)
     * with correct fields for each domain.  We have to do some light processing
     * to separate date groups in the field list, because they can be defined
     * with an aggregation function, such as my_date:week.
     * @protected
     * @param {Object} metaData
     * @returns {Object[]}
     */
    async _loadDataPoints(metaData) {
        const { measure, domains, fields, groupBy, resModel, cumulatedStart } = metaData;
        const fieldName = groupBy[0]?.fieldName;
        const sequential_field =
            cumulatedStart && SEQUENTIAL_TYPES.includes(fields[fieldName]?.type) ? fieldName : null;
        const sequential_spec = sequential_field && groupBy[0].spec;
        const measures = ["__count"];
        if (measure !== "__count") {
            let { group_operator, type } = fields[measure];
            if (type === "many2one") {
                group_operator = "count_distinct";
            }
            if (group_operator === undefined) {
                throw new Error(
                    `No aggregate function has been provided for the measure '${measure}'`
                );
            }
            measures.push(`${measure}:${group_operator}`);
        }

        const numbering = {}; // used to avoid ambiguity with many2one with values with same labels:
        // for instance [1, "ABC"] [3, "ABC"] should be distinguished.

        const proms = domains.map(async (domain, originIndex) => {
            const data = await this.orm.webReadGroup(
                resModel,
                domain.arrayRepr,
                measures,
                groupBy.map((gb) => gb.spec),
                {
                    lazy: false, // what is this thing???
                    context: { fill_temporal: true, ...this.searchParams.context },
                }
            );
            let start = false;
            if (
                cumulatedStart &&
                sequential_field &&
                data.groups.length &&
                domain.arrayRepr.some((leaf) => leaf.length === 3 && leaf[0] == sequential_field)
            ) {
                const first_date = data.groups[0].__range[sequential_spec].from;
                const new_domain = Domain.combine(
                    [
                        new Domain([[sequential_field, "<", first_date]]),
                        Domain.removeDomainLeaves(domain.arrayRepr, [sequential_field]),
                    ],
                    "AND"
                ).toList();
                start = await this.orm.webReadGroup(
                    resModel,
                    new_domain,
                    measures,
                    groupBy.filter((gb) => gb.fieldName != sequential_field).map((gb) => gb.spec),
                    {
                        lazy: false, // what is this thing???
                        context: { ...this.searchParams.context },
                    }
                );
            }
            const dataPoints = [];
            const cumulatedStartValue = {};
            if (start) {
                for (const group of start.groups) {
                    const rawValues = [];
                    for (const gb of groupBy.filter((gb) => gb.fieldName != sequential_field)) {
                        rawValues.push({ [gb.spec]: group[gb.spec] });
                    }
                    cumulatedStartValue[JSON.stringify(rawValues)] = group[measure];
                }
            }
            for (const group of data.groups) {
                const { __domain, __count } = group;
                const labels = [];
                const rawValues = [];
                for (const gb of groupBy) {
                    let label;
                    const val = group[gb.spec];
                    rawValues.push({ [gb.spec]: val });
                    const fieldName = gb.fieldName;
                    const { type } = fields[fieldName];
                    if (type === "boolean") {
                    	label = `${val}`; // toUpperCase?
                    	if(fieldName == 'check_in_out_state'){
                        	if(label == false || label == 'false'){
                        		label = 'Checked In'
                        	}else if(label == true || label == 'true'){
                        		label = 'Checked Out'
                        	}
                    	}
                    } else if (val === false) {
                        label = this._getDefaultFilterLabel(gb);
                    } else if (["many2many", "many2one"].includes(type)) {
                        const [id, name] = val;
                        const key = JSON.stringify([fieldName, name]);
                        if (!numbering[key]) {
                            numbering[key] = {};
                        }
                        const numbers = numbering[key];
                        if (!numbers[id]) {
                            numbers[id] = Object.keys(numbers).length + 1;
                        }
                        const num = numbers[id];
                        label = num === 1 ? name : `${name} (${num})`;
                    } else if (type === "selection") {
                        const selected = fields[fieldName].selection.find((s) => s[0] === val);
                        label = selected[1];
                    } else {
                        label = val;
                    }
                    labels.push(label);
                }

                let value = group[measure];
                if (value instanceof Array) {
                    // case where measure is a many2one and is used as groupBy
                    value = 1;
                }
                if (!Number.isInteger(value)) {
                    metaData.allIntegers = false;
                }
                const group_id = JSON.stringify(rawValues.slice(1));
                dataPoints.push({
                    count: __count,
                    domain: __domain,
                    value,
                    labels,
                    originIndex,
                    identifier: JSON.stringify(rawValues),
                    cumulatedStart: cumulatedStartValue[group_id] || 0,
                });
            }
            return dataPoints;
        });
        const promResults = await Promise.all(proms);
        return promResults.flat();
    }
});
