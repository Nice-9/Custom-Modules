odoo.define('sybyl_pos_fiscal_printer.PaymentScreen', function(require) {
    "use strict";

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    var _t = core._t;


    const FiscalPrinterPaymentScreen = PaymentScreen => class extends PaymentScreen {
        //@Override
        async validateOrder(isForceValidate) {
            var currentOrder = this.env.pos.get_order();
            var SubTotal = currentOrder.get_subtotal();

            if (SubTotal === 0) {
                this.showPopup('ErrorPopup', {
                    'title': this.env._t('Order With Zero'),
                    'body': this.env._t('Order Total must not be in Zero.'),
                });
                return false;
            } else {
                await this._finalizeValidation();
            }
        }
    };

    Registries.Component.extend(PaymentScreen, FiscalPrinterPaymentScreen);

    return FiscalPrinterPaymentScreen;
});
