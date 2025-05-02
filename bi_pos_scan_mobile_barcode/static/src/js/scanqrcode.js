//** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { onMounted, useRef, useState } from "@odoo/owl";
//import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";

export class scanqrcode extends AbstractAwaitablePopup {
    static template = "bi_pos_scan_mobile_barcode.scanqrcode";
    static defaultProps = {
        confirmText: _t("OK"),
        title: _t("Scanning QrCode"),
        body: '',
        cancelText: _t("Close"),
    };
    setup() {
        super.setup();
        this.pos = usePos();
        this.sound = useService("sound");
        this.popup = useService("popup");
        this.state = useState({
            codeFound: '',
        });
        onMounted(this.onMounted);
    }
    onMounted() {
        this._startCamera()
    }

    _startCamera() {
        var self = this
        var html5QrcodeScanner = false

        function onScanSuccess(decodedText, decodedResult) {
            // Handle on success condition with the decoded text or result.
            console.log(`Scan result: ${decodedText}`, decodedResult);
            if (self.pos.config.continue_scan) {
                if (decodedText) {
                    var product = ''
                    if (self.pos.config.scan_mobile_type == 'barcode') {
                        product = self.pos.db.get_product_by_barcode(decodedText);
                    } else if (self.pos.config.scan_mobile_type == 'int_ref') {
                        product = self.pos.db.product_by_default_code(decodedText);
                    } else if (self.pos.config.scan_mobile_type == 'qr_code') {
                        product = self.pos.db.product_by_qr(decodedText);
                    } else if (self.pos.config.scan_mobile_type == 'all') {
                        if (self.pos.db.get_product_by_barcode(decodedText)) {
                            product = self.pos.db.get_product_by_barcode(decodedText);
                        } else if (self.pos.db.product_by_default_code[decodedText]) {
                            product = self.pos.db.product_by_default_code[decodedText];
                        } else if (self.pos.db.product_by_qr[decodedText]) {
                            product = self.pos.db.product_by_qr[decodedText];
                        }
                    }
                    if (product) {
                        self.pos.get_order().add_product(product);
                        $.iaoAlert({
                            msg: "Product: " + product.display_name + " Added to cart successfully.",
                            type: "notification",
                            mode: "dark",
                            autoHide: true,
                            alertTime: "3000",
                            closeButton: true,
                        })
                        if (self.sound) {
                            self.sound.play("bell");
                        }
                    } else {
                        $.iaoAlert({
                            msg: "Warning: Scanned Internal Reference/Barcode not exist in any product!",
                            type: "error",
                            autoHide: true,
                            alertTime: "3000",
                            closeButton: true,
                            mode: "dark",
                        })
                        if (self.sound) {
                            self.sound.play("error");
                        }
                    }
                }
            } else {
                if (decodedText) {
                    var product = ''
                    if (self.pos.config.scan_mobile_type == 'barcode') {
                        product = self.pos.db.get_product_by_barcode(decodedText);
                    } else if (self.pos.config.scan_mobile_type == 'int_ref') {
                        product = self.pos.db.product_by_default_code(decodedText);
                    } else if (self.pos.config.scan_mobile_type == 'qr_code') {
                        product = self.pos.db.product_by_qr(decodedText);
                    } else if (self.pos.config.scan_mobile_type == 'all') {
                        if (self.pos.db.get_product_by_barcode(decodedText)) {
                            product = self.pos.db.get_product_by_barcode(decodedText);
                        } else if (self.pos.db.product_by_default_code(decodedText)) {
                            product = self.pos.db.product_by_default_code(decodedText);
                        } else if (self.pos.db.product_by_qr(decodedText)) {
                            product = self.pos.db.product_by_qr(decodedText);
                        }
                    }
                    if (product) {
                        self.pos.get_order().add_product(product);
                        html5QrcodeScanner.pause();
                        $.iaoAlert({
                            msg: "Product: " + product.display_name + " Added to cart successfully.",
                            type: "notification",
                            mode: "dark",
                            autoHide: true,
                            alertTime: "3000",
                            closeButton: true,
                        })
                        if (self.sound) {
                            self.sound.play("bell");
                        }
                    } else {
                        html5QrcodeScanner.pause();
                        $.iaoAlert({
                            msg: "Warning: Scanned Internal Reference/Barcode/Qrcode not exist in any product!",
                            type: "error",
                            autoHide: true,
                            alertTime: "3000",
                            closeButton: true,
                            mode: "dark",
                        })
                        if (self.sound) {
                            self.sound.play("error");
                        }
                    }
                }
            }
        }

        function onScanFailure(error) {
            // handle scan failure, usually better to ignore and keep scanning.
            // for example:
            console.warn(`Code scan error = ${error}`);
        }
        html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess, onScanFailure);
    }
}