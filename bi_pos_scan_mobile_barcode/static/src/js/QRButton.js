/** @odoo-module */

import { Component } from "@odoo/owl";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { scanqrcode } from "@bi_pos_scan_mobile_barcode/js/scanqrcode"
import { scanqrcodecustomer } from "@bi_pos_scan_mobile_barcode/js/scanqrcodecustomer"


export class QRButton extends Component {
    static template = "bi_pos_scan_mobile_barcode.QRButton";

    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }
    async onClick() {
        await this.popup.add(scanqrcode);
    }
    async onClickCustomer() {
        await this.popup.add(scanqrcodecustomer);
    }
}
ProductScreen.addControlButton({
    component: QRButton,
    condition: function() {
        return this.pos;
    },
});