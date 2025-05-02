from odoo import api, fields, models, _

class LoanClosureView(models.TransientModel):
    """ Model for managing loan requests."""
    _name = 'loan.closure.view'
    _description = "Loan Closure Reason view"

    closure_reason = fields.Many2one("loan.closure.reason",string="Reason",required=True)
    comment = fields.Text(string="Comment")
    loan_id = fields.Many2one("hr.loan")

    def loan_closure(self):
    	self.loan_id.write({'total_paid_amount':self.loan_id.total_amount,'balance_amount':0.00,'state':'close'})
    	message_body = f"Loan Closure Reason: {self.closure_reason.name}\n{self.comment}"
    	message_id=self.loan_id.with_context(mail_notify_author=True).message_post(
                            body=message_body,
                            message_type='comment',
                            partner_ids=[self.env.user.partner_id.id],
                        )