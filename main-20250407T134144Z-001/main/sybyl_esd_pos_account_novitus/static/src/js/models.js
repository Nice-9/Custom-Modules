odoo.define('sybyl_pos_fiscal_printer.employees', function(require) {
    "use strict";

    var models = require('point_of_sale.models');

    var super_order_model = models.Order.prototype;
    models.Order = models.Order.extend({
        init_from_JSON: function(json) {
            super_order_model.init_from_JSON.apply(this, arguments);
            this.fiscal_receipt_no = json.fiscal_receipt_no;
        },
    });
});