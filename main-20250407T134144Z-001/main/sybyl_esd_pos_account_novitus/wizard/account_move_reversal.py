# -*- coding: utf-8 -*-
from odoo import models


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def reverse_moves(self, is_modify):
        self.ensure_one()
        if self.move_ids.fiscal_receipt_no:
            # Full refund & Full Refund with New invoice - Will send xml data instead after wizard action.
            res = super(
                AccountMoveReversal, self.with_context(create_move_from_wizard=True)
            ).reverse_moves(is_modify)
        else:
            res = super(AccountMoveReversal, self).reverse_moves(is_modify)
        return res
