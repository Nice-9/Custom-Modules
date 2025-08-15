from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmStage(models.Model):
    _inherit = "crm.stage"

    requires_quotation = fields.Boolean(
        string="Requires Quotation (Opportunities)",
        help=(
            "If enabled, moving an opportunity into this stage will require at least "
            "one quotation linked to the opportunity. Leads are not affected."
        ),
    )


class CrmLead(models.Model):
    _inherit = "crm.lead"

    def _check_requires_quotation_before_stage(self, target_stage):
        """
        Raise UserError if any opportunity is being moved to a stage that requires a
        quotation but has none (excluding cancelled quotations).
        """
        if not target_stage or not target_stage.requires_quotation:
            return

        leads_to_check = self.filtered(lambda l: l.type == "opportunity")
        if not leads_to_check:
            return

        SaleOrder = self.env["sale.order"]
        missing = []
        for lead in leads_to_check:
            has_quotation = bool(
                SaleOrder.search_count(
                    [
                        ("opportunity_id", "=", lead.id),
                        ("state", "!=", "cancel"),
                    ],
                    limit=1,
                )
            )
            if not has_quotation:
                missing.append(lead)

        if missing:
            names = ", ".join(missing.mapped("name"))
            raise UserError(
                _(
                    "You cannot move the following opportunity(ies) to stage '%(stage)s' "
                    "until at least one quotation is created: %(names)s"
                )
                % {"stage": target_stage.name, "names": names}
            )

    def write(self, vals):
        if "stage_id" in vals:
            target_stage = self.env["crm.stage"].browse(vals["stage_id"])
            self._check_requires_quotation_before_stage(target_stage)
        return super().write(vals)

    def action_set_won(self, **kwargs):
        Stage = self.env["crm.stage"]
        by_team = {}
        for lead in self:
            key = lead.team_id.id or 0
            if key not in by_team:
                by_team[key] = Stage.search(
                    [
                        ("is_won", "=", True),
                        "|",
                        ("team_id", "=", False),
                        ("team_id", "=", lead.team_id.id),
                    ],
                    order="sequence asc, id asc",
                    limit=1,
                )
            target_stage = by_team[key]
            if target_stage:
                lead._check_requires_quotation_before_stage(target_stage)
        return super().action_set_won(**kwargs)
