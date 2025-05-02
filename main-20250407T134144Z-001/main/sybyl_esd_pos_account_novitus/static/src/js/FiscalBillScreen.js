odoo.define('sybyl_pos_fiscal_printer.FiscalBillScreen', function (require) {
    'use strict';

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const FiscalBillScreen = (ReceiptScreen) => {
        class FiscalBillScreen extends ReceiptScreen {
            confirm() {
                this.props.resolve({ confirmed: true, payload: null });
                this.trigger('close-temp-screen');
            }
            whenClosing() {
                this.confirm();
            }
            /**
             * @override
             */
            async printReceipt() {
            	console.log('Own custom');
                await super.printReceipt();
                this.currentOrder._printed = false;
            }
        }
        FiscalBillScreen.template = 'FiscalBillScreen';
        return FiscalBillScreen;
    };

    Registries.Component.addByExtending(FiscalBillScreen, ReceiptScreen);

    return FiscalBillScreen;
});
