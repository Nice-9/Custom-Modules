/** @odoo-module */

import { PosDB } from "@point_of_sale/app/store/db";
import { patch } from "@web/core/utils/patch";
import { unaccent } from "@web/core/utils/strings";

patch(PosDB.prototype, {
    constructor(options) {
        this.product_by_default_code = {};
        this.product_by_qr = {};
        console.log('___ this.product_by_qr : ', this.product_by_qr);
    },
    bi_add_product(products) {
        var self = this;
        var defined_product = false;
        for (var i = 0, len = products.length; i < len; i++) {
            var product = products[i];
            if (product.default_code) {
                self.product_by_default_code[product.default_code] = product;
            }
            if (product.qr_code) {
                self.product_by_qr[product.qr_code] = product;
            }
        }
    },
    get_product_by_default_code(default_code) {
        if (this.product_by_default_code[default_code]) {
            return this.product_by_default_code[default_code];
        } else {
            return undefined;
        }
    },
    get_product_by_qr(qr_code) {
        if (this.product_by_qr[qr_code]) {
            return this.product_by_qr[qr_code];
        } else {
            return undefined;
        }
    },
});