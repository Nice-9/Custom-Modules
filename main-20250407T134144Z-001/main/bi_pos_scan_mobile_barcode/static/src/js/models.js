/** @odoo-module */

import { Order, Orderline, Payment, Product } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { parseFloat as oParseFloat } from "@web/views/fields/parsers";

import {
    formatFloat,
    roundDecimals as round_di,
    roundPrecision as round_pr,
    floatIsZero,
} from "@web/core/utils/numbers";
import { ComboConfiguratorPopup } from "@point_of_sale/app/store/combo_configurator_popup/combo_configurator_popup";
patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        if(options.json){
            let product = options.pos.db.get_product_by_id(options.json.product_id)
            options['product'] = product

        }else{
            let product = options.pos.db.get_product_by_id(options.product.id)
            options['product'] = product
        }
        super.setup(...arguments);

    },
    get_unit() {
        var product = this.pos.db.get_product_by_id(this.product.id)
        return product.get_unit();
    },
    set_quantity(quantity, keep_price) {
        var product = this.pos.db.get_product_by_id(this.product.id)

        this.order.assert_editable();
        var quant =
            typeof quantity === "number" ? quantity : oParseFloat("" + (quantity ? quantity : 0));
        if (this.refunded_orderline_id in this.pos.toRefundLines) {
            const toRefundDetail = this.pos.toRefundLines[this.refunded_orderline_id];
            const maxQtyToRefund =
                toRefundDetail.orderline.qty - toRefundDetail.orderline.refundedQty;
            if (quant > 0) {
                this.env.services.popup.add(ErrorPopup, {
                    title: _t("Positive quantity not allowed"),
                    body: _t(
                        "Only a negative quantity is allowed for this refund line. Click on +/- to modify the quantity to be refunded."
                    ),
                });
                return false;
            } else if (quant == 0) {
                toRefundDetail.qty = 0;
            } else if (-quant <= maxQtyToRefund) {
                toRefundDetail.qty = -quant;
            } else {
                this.env.services.popup.add(ErrorPopup, {
                    title: _t("Greater than allowed"),
                    body: _t(
                        "The requested quantity to be refunded is higher than the refundable quantity of %s.",
                        this.env.utils.formatProductQty(maxQtyToRefund)
                    ),
                });
                return false;
            }
        }
        var unit = this.get_unit();
        if (unit) {
            if (unit.rounding) {
                var decimals = this.pos.dp["Product Unit of Measure"];
                var rounding = Math.max(unit.rounding, Math.pow(10, -decimals));
                this.quantity = round_pr(quant, rounding);
                this.quantityStr = formatFloat(this.quantity, {
                    digits: [69, decimals],
                });
            } else {
                this.quantity = round_pr(quant, 1);
                this.quantityStr = this.quantity.toFixed(0);
            }
        } else {
            this.quantity = quant;
            this.quantityStr = "" + this.quantity;
        }
        // just like in sale.order changing the quantity will recompute the unit price
        if (!keep_price && this.price_type === "original") {
            this.set_unit_price(
                product.get_price(
                    this.order.pricelist,
                    this.get_quantity(),
                    this.get_price_extra()
                )
            );
            this.order.fix_tax_included_price(this);
        }
        return true;
    },
});
