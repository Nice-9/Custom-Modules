odoo.define('sybyl_pos_fiscal_printer.TicketScreen', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');
    const { useAutofocus } = require('web.custom_hooks');
    const { posbus } = require('point_of_sale.utils');
    const { parse } = require('web.field_utils');
    const { useState, useContext } = owl.hooks;

    const FiscalPosTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            _getSearchFields() {
                const result = super._getSearchFields();
                const fields = {
                    FISCAL_RECEIPT_NUMBER: {
                        repr: (order) => order.fiscal_receipt_no,
                        displayName: this.env._t('Fiscal Receipt Number'),
                        modelField: 'fiscal_receipt_no',
                    },
                };
                var merged = Object.assign({}, result, fields);
                return merged;
            }
        };

    Registries.Component.extend(TicketScreen, FiscalPosTicketScreen);
});