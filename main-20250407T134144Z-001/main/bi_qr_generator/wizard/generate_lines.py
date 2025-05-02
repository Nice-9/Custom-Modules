from odoo import models, fields, api


class GenarteQRLines(models.TransientModel):
    _name = 'generate.qrcode.lines'
    _description = 'Generate QR Code Lines'

    widget_id = fields.Many2one(comodel_name="generate.qrcode", string="Widget")
    default_code = fields.Char(string="Internal Reference")
    name = fields.Char(string="Product Name")
    list_price = fields.Float(string="Sale Price")
    standard_price = fields.Float(string="Cost Price")
    categ_id = fields.Many2one('product.category', 'Product Category',)
    type = fields.Selection([('consu', 'Consumable'),('service', 'Service'),('product','Storable  Product')],
                            string='Product Type', default='consu', required=True)
    qr_code = fields.Char(string="QR Code")
