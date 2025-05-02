odoo.define('sybyl_pos_fiscal_printer.pos_fiscal_printer', function(require) {
    'use strict'

    var models = require('point_of_sale.models')
    var FiscalPrinter = require('sybyl_pos_fiscal_printer.FiscalPrinter')

    var posmodelSuper = models.PosModel.prototype
    models.PosModel = models.PosModel.extend({
        after_load_server_data: function() {
            var self = this
            return posmodelSuper.after_load_server_data.apply(this, arguments).then(function() {
                if (self.config.other_devices && self.config.iface_fiscal_printer_ip_address && !self.config.epson_printer_ip) {
                    self.proxy.printer = new FiscalPrinter(self.config.iface_fiscal_printer_ip_address, self)
                }
            })
        }
    })
})