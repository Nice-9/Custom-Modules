from datetime import timedelta
import pytz
from odoo import api, fields, models, _
from odoo.osv.expression import AND
import re

class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        result = super().get_sale_details(date_start=date_start, date_stop=date_stop, config_ids=config_ids, session_ids=session_ids)
        domain = [('state', 'in', ['paid', 'invoiced', 'done'])]
        if session_ids:
            domain = AND([domain, [('session_id', 'in', session_ids)]])
        else:
            if date_start:
                date_start = fields.Datetime.from_string(date_start)
            else:
                user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
                today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
                date_start = today.astimezone(pytz.timezone('UTC')).replace(tzinfo=None)

            if date_stop:
                date_stop = fields.Datetime.from_string(date_stop)
                if date_stop < date_start:
                    date_stop = date_start + timedelta(days=1, seconds=-1)
            else:
                date_stop = date_start + timedelta(days=1, seconds=-1)

            domain = AND([domain,
                          [('date_order', '>=', fields.Datetime.to_string(date_start)),
                           ('date_order', '<=', fields.Datetime.to_string(date_stop))]])

            if config_ids:
                domain = AND([domain, [('config_id', 'in', config_ids)]])

        orders = self.env['pos.order'].search(domain)
        payment_ids = self.env["pos.payment"].search([("pos_order_id", "in", orders.ids)]).ids

        payments = []
        config_names = []
        if payment_ids:
            query = "SELECT id, name FROM pos_config WHERE id IN %s"
            self.env.cr.execute(query, (tuple(config_ids),))
            config_data = self.env.cr.fetchall()
            config_dict = {row[0]: row[1] for row in config_data}
            config_names = list(config_dict.values())

            def sanitize_column_name(name):
                return re.sub(r'\W+', '_', name)

            sanitized_config_names = {sanitize_column_name(name): name for name in config_dict.values()}

            config_columns = ", ".join(
                [f"SUM(CASE WHEN session.config_id = {config_id} THEN amount ELSE 0 END) AS {sanitize_column_name(config_name)}"
                 for config_id, config_name in config_dict.items()]
            )

            dynamic_query = f"""
                SELECT 
                    method.name, 
                    {config_columns},
                    SUM(amount) AS total
                FROM pos_payment AS payment
                JOIN pos_payment_method AS method ON payment.payment_method_id = method.id
                JOIN pos_session AS session ON payment.session_id = session.id
                JOIN pos_config AS config ON session.config_id = config.id
                WHERE payment.id IN %s
                GROUP BY method.name
            """

            self.env.cr.execute(dynamic_query, (tuple(payment_ids),))
            results = self.env.cr.fetchall()
            columns = ['name'] + list(sanitized_config_names.keys()) + ['total']
            processed_results = []

            for row in results:
                result_dict = {}
                for col_name, value in zip(columns, row):
                    if col_name in sanitized_config_names:
                        result_dict[sanitized_config_names[col_name]] = value
                    else:
                        result_dict[col_name] = value
                processed_results.append(result_dict)

            payments = processed_results
        result.update({'payments_config_wise': payments, 'config_names_choosed': config_names})
        return result
