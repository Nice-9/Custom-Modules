
import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api


class GenarteQR(models.TransientModel):
    _name = 'generate.qrcode'
    _description = 'Generate QR Code'

    widget_ids = fields.One2many(comodel_name="generate.qrcode.lines", string="Widget Lines", inverse_name="widget_id")
    override_qr = fields.Boolean(string='Override QR Code')
    qr_code = fields.Char(string="QR Code")

    _sql_constraints = [
        ('unique_qrcode_widget', 'unique (qr_code)', 'QR Code address already exists!')
    ]

    @api.model
    def default_get(self, fields):
        # return self.env['product.template'].browse(self._context.get('active_ids'))
        res = super(GenarteQR, self).default_get(fields)
        active_ids = self._context.get('active_ids', []) or []
        active_model = self._context.get('active_model')
        qr_line_ids = []
        if active_model == 'product.template':
            for record in self.env['product.template'].browse(active_ids):
                vals = {
                    'default_code' : record.default_code,
                    'name' : record.name,
                    'list_price' : record.list_price,
                    'standard_price' : record.standard_price,
                    'categ_id' : record.categ_id,
                    'type' : record.type,
                    'qr_code' : record.qr_code,
                    'widget_id' : self.id
                }
                qr_line_ids.append((0,0,vals))
            res['widget_ids'] = qr_line_ids
            return res
        if active_model == 'product.product':
            for record in self.env['product.product'].browse(active_ids):
                vals = {
                    'default_code': record.default_code,
                    'name': record.name,
                    'list_price': record.list_price,
                    'standard_price': record.standard_price,
                    'categ_id': record.categ_id,
                    'type': record.type,
                    'qr_code': record.qr_code,
                    'widget_id': self.id
                }

                qr_line_ids.append((0, 0, vals))
            res['widget_ids'] = qr_line_ids
            return res

    def generate_qrcode(self):
        active_ids = self._context.get('active_ids', []) or []
        active_model = self._context.get('active_model')
        if active_model == 'product.template':
            for record in self.env['product.template'].browse(active_ids):
                if self.override_qr:
                    record.qr_code = self.env['ir.sequence'].next_by_code('product.template')
                    self.qr_code = record.qr_code
                else:
                    if not record.qr_code:
                        record.qr_code = self.env['ir.sequence'].next_by_code('product.template')
                        self.qr_code = record.qr_code
        if active_model == 'product.product':
            for record in self.env['product.product'].browse(active_ids):
                if self.override_qr:
                    record.qr_code = self.env['ir.sequence'].next_by_code('product.template')
                    self.qr_code = record.qr_code
                else:
                    if not record.qr_code:
                        record.qr_code = self.env['ir.sequence'].next_by_code('product.template')
                        self.qr_code = record.qr_code

