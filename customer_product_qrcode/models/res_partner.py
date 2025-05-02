# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartners(models.Model):
    """Extends the res partner model to include QR code functionality."""
    _inherit = 'res.partner'

    def _default_qr(self):
        if 'default_parent_id' in self._context:
            partner = self.env['res.partner'].browse(int(self._context.get('default_parent_id')))
            return partner.qr
        return False

    def _default_sequence(self):
        if 'default_parent_id' in self._context:
            partner = self.env['res.partner'].browse(int(self._context.get('default_parent_id')))
            return partner.qr_sequence
        return False

    def _get_relationship(self):
        return [("spouse", "Spouse"),("son", "Son"),("daughter", "Daughter"),("father", "Father"),("mother", "Mother"),("in_law", "In Law"),("brother", "Brother"),("sister", "Sister"),("cousin", "Cousin"),("nephew", "Nephew"),("uncle", "Uncle"),("aunt", "Aunt"),("grand_parent", "Grand Parent")]

    qr_sequence = fields.Char(string="Reference ID", readonly=True,default=_default_sequence)
    qr = fields.Binary(string="QR Code", help='Used for Qr code',default=_default_qr)
    qr_sent_by_email = fields.Boolean(default=False)
    relation_contact = fields.Selection(selection=_get_relationship, string="Relationship")

    def init(self):
        """Initialize the QR sequence for customer partners with a combination
        of 'DEF', partner's name (without spaces), and partner's ID."""
        for record in self.env['res.partner'].search(
                [('customer_rank', '=', True)]):
            name = record.name.replace(" ", "")
            record.qr_sequence = 'DEF' + name.upper() + str(record.id)

    @api.model
    def create(self, vals):
        """Create a new partner record and assign a unique QR sequence to it."""
        prefix = self.env['ir.config_parameter'].sudo().get_param(
            'customer_product_qr.config.customer_prefix')
        if not prefix:
            raise UserError(_('Set A Customer Prefix In General Settings'))
        prefix = str(prefix)
        result = super(ResPartners, self).create(vals)
        if result.parent_id:
            result.sudo().write({
                'qr_sequence':result.parent_id.qr_sequence,
                'qr':result.parent_id.qr
                })
        else:
            seq = prefix + self.env['ir.sequence'].next_by_code(
                'res.partner') or '/'
            vals['qr_sequence'] = seq
        return result

    @api.depends('qr_sequence')
    def generate_qr(self):
        """Generate a QR code based on the partner's qr_sequence and store it in
        the 'qr' field of the partner record."""
        if qrcode and base64:
            if not self.qr_sequence:
                prefix = self.env['ir.config_parameter'].sudo().get_param(
                    'customer_product_qr.config.customer_prefix')
                if not prefix:
                    raise UserError(
                        _('Set A Customer Prefix In General Settings'))
                prefix = str(prefix)
                self.qr_sequence = prefix + self.env['ir.sequence'].next_by_code(
                    'res.partner') or '/'
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.qr_sequence)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            self.write({'qr': qr_image})

            if self.qr:
                for rec in self.child_ids:
                    rec.write({'qr': qr_image,'qr_sequence':self.qr_sequence})
            return self.env.ref(
                'customer_product_qrcode.print_qr').report_action(self, data={
                 'data': self.id, 'type': 'cust'})
        else:
            raise UserError(
                _('Necessary Requirements To Run This Operation Is Not '
                  'Satisfied'))

    def get_qr_code_download_url(self):
        return f"/web/content/{self._name}/{self.id}/qr?download=true"

    def get_partner_by_qr(self, **args):
        """THis fn is to get partner by qr """
        return self.env['res.partner'].search([('qr_sequence', '=', self.id), ],
                                              limit=1).id

    def send_qr_code_by_email(self):
        self.ensure_one()
        mail_template_id = self.env.ref(
            "customer_product_qrcode.mail_template_send_qr_by_email"
        )
        # Decode the base64 QR code to binary data
        if not self.qr:
            raise UserError(_("Please generate a QR code before it can be sent by email."))
        qr_data = base64.b64decode(self.qr)

        # Prepare attachment values
        ir_values = {
            'name': 'Karura Forest Entry QR - ' + self.name,
            'type': 'binary',
            'datas': base64.b64encode(qr_data).decode('utf-8'),  # Re-encode as base64 for Odoo
            'store_fname': 'entry_qr_' + self.name + '.png',
            'mimetype': 'image/png',
        }

        # Create the attachment
        qr_attachment = self.env['ir.attachment'].sudo().create(ir_values)

        # Attach the created attachment to the email template
        mail_template_id.attachment_ids = [(5,0,0)]
        mail_template_id.attachment_ids = [(4, qr_attachment.id)]
        mail_template_id.send_mail(self.id, force_send=True)
        self.qr_sent_by_email = True
        
