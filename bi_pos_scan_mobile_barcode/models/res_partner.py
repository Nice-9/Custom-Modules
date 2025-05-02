# -*- coding: utf-8 -*-

import datetime

from odoo import models, fields, api
from odoo.addons.resource.models.utils import Intervals


class ResPartners(models.Model):
    _inherit = "res.partner"

    subscription_ids = fields.One2many(
        "sale.order", "partner_id", string="Subscriptions"
    )
    subscription_expiry_date = fields.Date()
    subscription_state = fields.Boolean(
        "Is User Subscribed", compute="_compute_subscription_state"
    )
    subscription_state_store = fields.Boolean()
    # subscription_state = fields.Selection(
    #     selection=[("active", "Active"), ("expired", "Expired")],
    #     string="Subscription Status", compute_sudo=True,
    #     store=True,
    #     compute="_compute_subscription_state",
    # )
    check_in_out_state = fields.Boolean(default=True)
    # check_in_out_state = fields.Selection(
    #    selection=[
    #         ("check_in", "Check In"),
    #         ("check_out", "Check Out"),
    #     ],
    #     string="Check In/Out Status",
    #     default="check_out",
    #     required=True,
    # )
    partner_checkin_history_ids = fields.One2many(
        "partner.checkin.history", "partner_id"
    )
    partner_checkin_log_ids = fields.One2many("partner.checkin.log", "partner_id")
    has_subscription = fields.Boolean(default=False,compute="_check_subscription",store=True)

    @api.depends("subscription_count")
    def _check_subscription(self):
        for rec in self:
            if rec.subscription_count > 0:
                rec.has_subscription = True
            elif rec.parent_id.subscription_count > 0:
                rec.has_subscription = True
            else:
                rec.has_subscription = False


    def update_customer_sign_in_out_status(self, customer_checklist_dict):
        if customer_checklist_dict:
            for customer in customer_checklist_dict.get('customer_checklist_dict'):
                partner_id = None
                dog_id = None
                car_id = None
                if customer.get("id"):
                    partner_id = (
                        self.env["res.partner"].sudo().browse(customer.get("id"))
                    )
                elif customer.get("dog_id"):
                    dog_id = (
                        self.env["subscription.dog"].sudo().browse(customer.get("dog_id"))
                    )
                else:
                    car_id = (
                        self.env["subscription.vehicle"].sudo().browse(customer.get("car_id"))
                    )

                if customer.get("checked"):
                    self.env["partner.checkin.history"].sudo().toggle_check_in_out(
                        partner_id,dog_id,car_id
                    )
                    if partner_id:
                        self.state_update_data(partner_id)
                        
                    elif dog_id:
                        # dog_id
                        self.state_update_data(dog_id)
                    else:
                        self.state_update_data(car_id)
                self.env["partner.checkin.log"].sudo().create(
                    {
                        "partner_id": partner_id.id if partner_id else None,
                        "dog_id": dog_id.id if dog_id else None,
                        "car_id": car_id.id if car_id else None,
                        "state": customer.get("checked"),
                    }
                )
            return {"state": "updated"}
        return {"state": "no_change"}
    
    def state_update_data(self, data_id):
        if data_id.check_in_out_state:
            data_id.check_in_out_state = False
        else:
            data_id.check_in_out_state = True

    def toggle_check_in_out(self):
        for record in self:
            if record.check_in_out_state:
                record.check_in_out_state = False
            else:
                record.check_in_out_state = True
            # if record.check_in_out_state == "check_in":
            #     record.check_in_out_state = "check_out"
            # elif record.check_in_out_state == "check_out":
            #     record.check_in_out_state = "check_in"

    @api.depends("subscription_expiry_date")
    def _compute_subscription_state(self):
        for record in self:
            if (
                record.subscription_expiry_date
                and record.subscription_expiry_date > datetime.datetime.now().date()
            ):
                # record.subscription_state = "active"
                record.sudo().subscription_state = True
                record.sudo().subscription_state_store = True
            else:
                record.sudo().subscription_state = False
                record.sudo().subscription_state_store = False
                # record.subscription_state = "expired"

    @api.model
    def auto_check_out_records(self):
        # Search for all records (Contacts, Dogs, and Cars) with status 'CHECK-IN'
        check_in_records = self.env['res.partner'].sudo().search([('check_in_out_state', '=', False)])

        # Update their status to 'CHECK-OUT'
        for record in check_in_records:
            last_updated_partner_id = self.env['partner.checkin.history'].search(
                [("partner_id", "=", record.id)], limit=1, order="id desc"
            )
            last_updated_partner_id.update(
                {
                    "check_out": fields.Datetime.now(),
                    "parent_id" : record.parent_id.id if record.parent_id.id else record.id
                }
            )
            record.check_in_out_state = True
            for dog in record.dog_ids:
                last_updated_dog_id = self.env['partner.checkin.history'].search(
                    [("dog_id", "=", dog.id)], limit=1, order="id desc"
                )
                last_updated_dog_id.update(
                    {
                        "check_out": fields.Datetime.now(),
                        "parent_id": dog.owner_id.id
                    }
                )
                dog.check_in_out_state = True
            for car in record.car_ids:
                last_updated_car_id = self.env['partner.checkin.history'].search(
                    [("car_id", "=", car.id)], limit=1, order="id desc"
                )
                last_updated_car_id.update(
                    {
                        "check_out": fields.Datetime.now(),
                        "parent_id": car.owner_id.id
                    }
                )
                car.check_in_out_state = True

class PartnersCheckinLog(models.Model):
    _name = "partner.checkin.log"
    _description = "Partner Checkin Log"

    partner_id = fields.Many2one("res.partner", string="Customer")
    state = fields.Char()
    dog_id = fields.Many2one("subscription.dog", string="Dog")
    car_id = fields.Many2one("subscription.vehicle", string="Car")


class PartnersCheckinHistory(models.Model):
    _name = "partner.checkin.history"
    _description = "Partner Checkin History"
    _order = 'check_in desc'

    partner_id = fields.Many2one("res.partner", string="Customer")
    check_in = fields.Datetime(
        string="Check In Date", default=fields.Datetime.now, required=True
    )
    check_out = fields.Datetime(string="Check Out Date")
    dog_id = fields.Many2one("subscription.dog", string="Dog")
    car_id = fields.Many2one("subscription.vehicle", string="Car")
    parent_id = fields.Many2one("res.partner")

    def toggle_check_in_out(self, partner_id, dog_id, car_id):
        if partner_id:
            last_updated_partner_id = self.search(
                [("partner_id", "=", partner_id.id)], limit=1, order="id desc"
            )
            if partner_id.subscription_count > 0:
                partner_id.update({"has_subscription": True})
            elif partner_id.parent_id.subscription_count > 0:
                partner_id.update({"has_subscription": True})
            else:
                partner_id.update({"has_subscription": False})
            if not last_updated_partner_id or last_updated_partner_id.check_out:
                last_updated_partner_id.create(
                    {
                        "partner_id": partner_id.id,
                        "dog_id": None,
                        "car_id": None,
                        "parent_id" : partner_id.parent_id.id if partner_id.parent_id.id else partner_id.id 
                    }
                )
            else:
                if last_updated_partner_id and partner_id.check_in_out_state:
                    last_updated_partner_id.create(
                        {
                            "partner_id": partner_id.id,
                            "dog_id": None,
                            "car_id": None,
                            "parent_id" : partner_id.parent_id.id if partner_id.parent_id.id else partner_id.id 
                        }
                    )
                else:
                    last_updated_partner_id.update(
                        {
                            "check_out": fields.Datetime.now(),
                            "parent_id" : partner_id.parent_id.id if partner_id.parent_id.id else partner_id.id
                        }
                    )
        elif dog_id:
            last_updated_dog_id = self.search(
                [("dog_id", "=", dog_id.id)], limit=1, order="id desc"
            )
            dog_id.update({'subscription_count':dog_id.owner_id.subscription_count})
            if not last_updated_dog_id or last_updated_dog_id.check_out:
                self.create(
                    {
                        "dog_id": dog_id.id,
                        "partner_id": None,
                        "car_id": None,
                        "parent_id": dog_id.owner_id.id
                    }
                )
            else:
                if last_updated_dog_id and dog_id.check_in_out_state:
                    last_updated_dog_id.create(
                    {
                        "dog_id": dog_id.id,
                        "partner_id": None,
                        "car_id": None,
                        "parent_id": dog_id.owner_id.id
                    }
                )
                else:
                    last_updated_dog_id.update(
                        {
                            "check_out": fields.Datetime.now(),
                            "parent_id": dog_id.owner_id.id
                        }
                    )
        elif car_id:
            last_updated_car_id = self.search(
                [("car_id", "=", car_id.id)], limit=1, order="id desc"
            )
            car_id.update({'subscription_count':car_id.owner_id.subscription_count})
            if not last_updated_car_id or last_updated_car_id.check_out:
                self.create(
                    {
                        "car_id": car_id.id,
                        "partner_id": None,
                        "dog_id": None,
                        "parent_id": car_id.owner_id.id
                    }
                )
            else:
                if last_updated_car_id and car_id.check_in_out_state:
                    last_updated_car_id.create(
                        {
                            "car_id": car_id.id,
                            "partner_id": None,
                            "dog_id": None,
                            "parent_id": car_id.owner_id.id
                        }
                    )
                else:
                    last_updated_car_id.update(
                        {
                            "check_out": fields.Datetime.now(),
                            "parent_id": car_id.owner_id.id
                        }
                    )

    checkin_hours = fields.Float(
        compute="_compute_checkin_hours",
        store=True,
        readonly=True,
        string="Hours Spent"
    )

    @api.depends("check_in", "check_out")
    def _compute_checkin_hours(self):
        for record in self:
            if record.check_out and record.check_in:
                record_intervals = Intervals(
                    [(record.check_in, record.check_out, record)]
                )
                delta = sum((i[1] - i[0]).total_seconds() for i in record_intervals)
                record.checkin_hours = delta / 3600.0
            else:
                record.checkin_hours = False


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _web_read_group(self, domain, fields, groupby, limit=None, offset=0, orderby=False, lazy=True):
        """
        See ``web_read_group`` for params description.

        :returns: array of groups
        """
        if 'check_in_out_state' in groupby and self._name == 'res.partner':
            domain += [('has_subscription','=',True)]

        if 'check_in_out_state' in groupby and self._name in ('subscription.dog','subscription.vehicle'):
            domain += [('subscription_count','>',0)]
        groups = self.read_group(domain, fields, groupby, offset=offset, limit=limit,
                                 orderby=orderby, lazy=lazy)
        return groups

# class SubscriptionDog(models.Model):
#     _inherit = "subscription.dog"

#     partner_checkin_history_ids = fields.Many2many("partner.checkin.history",compute="_fetch_dogs_data")

#     def _fetch_dogs_data(self):
#         records = self.env['partner.checkin.history'].search([('dog_id','=',self.id)])

# class SubscriptionVehicle(models.Model):
#     _inherit = "subscription.vehicle"

#     partner_checkin_history_ids = fields.Many2many("partner.checkin.history")