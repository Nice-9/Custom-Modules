# -*- coding: utf-8 -*-

import base64
import json
import logging
import time

import requests
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare
from requests.auth import HTTPBasicAuth

from odoo import api, fields, models, _

from ..controllers.dibon_sms_client import DibonSMSClient

_logger = logging.getLogger(__name__)


class MpesaOnlineTransaction(models.Model):
    _inherit = "payment.transaction"

    mpesa_online_merchant_request_id = fields.Char(
        "MPESA Merchant Request ID",
        readonly=True,
        help="MPESA transaction reference/receipt number",
    )
    mpesa_online_checkout_request_id = fields.Char(
        "MPESA Checkout Request ID", readonly=True
    )
    mpesa_online_time_stamp = fields.Char("MPESA Time Stamp", readonly=True)
    mpesa_online_password = fields.Char("MPESA Password", readonly=True)
    mpesa_online_currency_id = fields.Many2one(
        related="provider_id.mpesa_online_currency_id", string="Currency(Mpesa)"
    )
    provider = fields.Selection(related="provider_id.code", readonly=True)
    
    # Add new fields to store callback data
    mpesa_payment_phone = fields.Char("Payment Phone Number", readonly=True)
    mpesa_receipt = fields.Char("MPesa Receipt Number", readonly=True)
    mpesa_phone = fields.Char('Mpesa Phone No', readonly=True)  # Updated field title
    mpesa_initiating_phone = fields.Char('Initiating Phone Number', readonly=True)  # New field

    def _handle_feedback_data(self, data):
        """Handle manual payment submission and STK push callback data"""
        super()._handle_feedback_data(data)
        if self.provider_code != 'mpesa_online':
            return

        _logger.info("MPESA_PAYMENT: Processing payment data: %s", data)
        
        # Handle manual payment submission
        if data.get('manual_payment'):
            self._process_manual_payment(data)
        else:
            # Handle STK push callback (existing code)
            self._process_stk_callback(data)

    def _process_manual_payment(self, data):
        """Process manual payment submission"""
        _logger.info("MPESA_MANUAL: Processing manual payment submission")
        
        # Update transaction with manual payment details
        vals = {
            'mpesa_receipt': data.get('mpesa_receipt'),
            'mpesa_phone': data.get('mpesa_phone_number'),
            'state': 'pending',  # Set to pending for manual verification
            'last_state_change': fields.Datetime.now(),
        }
        self.write(vals)
        
        # Send notifications
        self._send_manual_payment_notifications()
        
        _logger.info("MPESA_MANUAL: Payment details saved and notifications sent")
        return True

    def _send_manual_payment_notifications(self):
        """Send SMS notifications for manual payment"""
        try:
            sms_config = self.env['mpesa.sms.config'].search([('is_enabled', '=', True)], limit=1)
            if not sms_config:
                _logger.warning("MPESA_NOTIFY: No active SMS configuration found")
                return False

            # Customer notification
            customer_message = (
                "Dear Customer, your payment details have been received.\n"
                f"Amount: KES {self.amount}\n"
                f"Reference: {self.reference}\n"
                "Please wait for confirmation."
            )
            
            # Admin notification
            admin_phone = self.provider_id.admin_notification_phone
            if admin_phone:
                admin_message = (
                    "New manual MPesa payment received\n"
                    f"Amount: KES {self.amount}\n"
                    f"MPesa Receipt: {self.mpesa_receipt}\n"
                    f"Phone: {self.mpesa_phone}\n"
                    f"Reference: {self.reference}\n"
                    "Please verify and confirm."
                )

                # Send notifications using SMS client
                client = DibonSMSClient(sms_config.api_key)
                
                # Send to customer
                client.send_sms(
                    sender=sms_config.sender_id,
                    recipient=self.mpesa_phone,
                    message=customer_message,
                    ref_id=f"{self.reference}_cust"
                )
                
                # Send to admin
                client.send_sms(
                    sender=sms_config.sender_id,
                    recipient=admin_phone,
                    message=admin_message,
                    ref_id=f"{self.reference}_admin"
                )
                
                _logger.info("MPESA_NOTIFY: Notifications sent successfully")
                return True

        except Exception as e:
            _logger.error("MPESA_NOTIFY: Failed to send notifications: %s", str(e))
            return False

    def _process_stk_callback(self, data):
        """Process STK push callback data"""
        _logger.info("MPesa Callback: Processing payment from phone number: %s", data.get('phone'))
        
        # Only update if callback data has phone number
        if data.get('phone'):
            self.write({
                'mpesa_phone': data.get('phone'),
                'mpesa_payment_phone': data.get('phone'),
                'mpesa_receipt': data.get('receipt'),
            })
            _logger.info("MPesa Callback: Updated transaction with callback phone: %s and receipt: %s", 
                        data.get('phone'), data.get('receipt'))
        else:
            _logger.info("MPesa Callback: No phone number in callback data, keeping existing phone: %s",
                        self.mpesa_phone)

    @api.model
    def _mpesa_online_form_get_tx_from_data(self, data):
        reference, currency, acquirer = (
            data.get("reference"),
            data.get("currency"),
            data.get("acquirer"),
        )
        txn = self.search(
            [
                ("reference", "=", reference),
                ("acquirer_id", "=", int(acquirer)),
                ("currency_id", "=", int(currency)),
            ]
        )
        if not txn or len(txn) > 1:
            error_msg = "MPESA_ONLINE: Received data for Order reference %s" % reference
            if not txn:
                error_msg += "; but no transaction found"
            else:
                error_msg += "; but multiple transactions found"
            _logger.error(error_msg)
        return txn

    def _mpesa_online_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        # compare amount paid vs amount of the order
        if float_compare(float(data.get("amount")), (self.amount + self.fees), 2) != 0:
            invalid_parameters.append(
                ("amount", data.get("amount"), "%.2f" % self.amount)
            )

            # compare currency
        if int(data.get("currency")) != self.currency_id.id:
            invalid_parameters.append(
                ("currency", data.get("currency"), self.currency_id.id)
            )

            # compare acquirer
        if int(data.get("acquirer")) != self.provider_id.id:
            invalid_parameters.append(
                ("acquirer", data.get("acquirer"), self.provider_id.id)
            )

            # compare order reference
        if str(data.get("reference")) != self.reference:
            invalid_parameters.append(
                ("reference", data.get("reference"), self.reference)
            )

        return invalid_parameters

    def mpesa_online_message_validate(self, pay=None, vals=None):
        """Called when the mpesa online callback url receives data from safaricom mpesa API.
        Validates payment and return dict of values to be used to update the payment transaction.
        """
        if pay:
            pay.write(
                {
                    "reconciled": True,
                    "acquirer_id": self.provider_id.id,
                    "currency_id": self.provider_id.mpesa_online_currency_id.id,
                }
            )
            vals["date"] = fields.Datetime.now()
            vals["acquirer_reference"] = pay.display_name
            msg = _("MPESA_ONLINE: Customer paid")
            msg += " %s %s" % (pay.amount, self.mpesa_online_currency_id.name)
            msg += _(" against an order amounting to")
            msg += " %s %s" % (self.amount, self.currency_id.name)
            _logger.info(msg)
            amount_to_pay = self.amount
            # multi-currency support
            if self.provider_id.mpesa_online_currency_id.id != self.currency_id.id:
                amount_to_pay = self.currency_id._convert(
                    from_amount=self.amount,
                    company=self.partner_id.company_id,
                    to_currency=self.provider_id.mpesa_online_currency_id,
                    date=fields.Date.today(),
                )
            res = float_compare(
                pay.amount, amount_to_pay, self.provider_id.mpesa_online_dp
            )
            if res == 0:
                msg = _(
                    "MPESA_ONLINE: Payment successfully confirmed.Customer paid precise amount"
                )
                vals["state"] = "done"
                vals["state_message"] = msg
                _logger.info(msg)

            elif res == 1:
                delta = pay.amount - amount_to_pay
                msg = _(
                    "MPESA_ONLINE: Payment successfully confirmed."
                    "Customer paid more than the order amount by"
                )
                msg += " %s %s" % (
                    pay.currency_id.symbol or "",
                    "{:,.2f}".format(delta),
                )
                vals["state_message"] = msg
                vals["state"] = "done"
                _logger.info(msg)
            else:
                delta = amount_to_pay - pay.amount
                msg = _(
                    "MPESA_ONLINE: Payment validated but order not confirmed."
                    "Customer paid less than the order amount by"
                )
                msg += " %s %s" % (
                    pay.currency_id.symbol or "",
                    "{:,.2f}".format(delta),
                )
                vals["state"] = "pending"
                vals["state_message"] = msg
                _logger.info(msg)
        return vals

    def _mpesa_online_form_validate(self, data):
        # there will be not tx_id in data for portal case. Hence we need to
        # check and update before proceeding
        if not (data.get("tx_id", False)):
            data.update(tx_id=self.id)
        acq = self.env["payment.provider"].browse([int(data.get("acquirer"))])
        if not acq:
            return False
        return acq.mpesa_stk_push(data)

    def _send_payment_request(self):
        super()._send_payment_request()
        if self.provider_code != "mpesa_online":
            return
        return

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "mpesa_online" or len(tx) == 1:
            return tx

        tx = self.search(
            [
                ("reference", "=", notification_data.get("reference")),
                ("provider_code", "=", "mpesa_online"),
            ]
        )
        if not tx:
            raise ValidationError(
                "MPesa: "
                + _(
                    "No transaction found matching reference %s.",
                    notification_data.get("reference"),
                )
            )
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != "mpesa_online":
            return

        _logger.info(notification_data.get("phoneNumber"))
        _logger.info(self.amount)

        phone_number = self.format_phone(notification_data.get("phoneNumber"))
        stk_response = self.trigger_stk_push(
            self.provider_id, phone_number, self.amount
        )
        notification_data = {**notification_data, **stk_response}
        state = notification_data["payment_state"]
        if state == "pending":
            self._set_pending()
        elif state == "done":
              # Send SMS notification for successful transaction
            self._send_transaction_sms()
            if self.capture_manually and not notification_data.get("manual_capture"):
                self._set_authorized()
            else:
                self._set_done()
                if self.operation == "refund":
                    self.env.ref("payment.cron_post_process_payment_tx")._trigger()
        elif state == "cancel":
            self._set_canceled()
        else:  # Simulate an error state.
            self._set_error(
                _(
                    "%s",
                    notification_data.get("error_message"),
                )
            )

    def format_phone(self, phone):
        formatted_phone = (
            f"254{phone}"
        )
        return formatted_phone

    def get_timestamp_passkey(self, short_code, pass_key):
        time_stamp = str(time.strftime("%Y%m%d%H%M%S"))
        if not short_code or not pass_key:
            raise ValidationError(_("Please check the configuration!"))
        passkey = short_code + pass_key + time_stamp
        password = str(base64.b64encode(passkey.encode("utf-8")), "utf-8")
        return time_stamp, password

    def _mpesa_get_access_token(self, customer_key, secrete_key, test_mode):
        try:
            url = (
                "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
                if not test_mode
                else "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            )
            _logger.info("MPESA_TOKEN: Attempting to get access token from URL: %s", url)
            _logger.info("MPESA_TOKEN: Using customer key: %s", customer_key)
            
            response = requests.get(
                url,
                auth=HTTPBasicAuth(customer_key, secrete_key),
                timeout=30,
            )
            _logger.info("MPESA_TOKEN: Response status code: %s", response.status_code)
            _logger.info("MPESA_TOKEN: Response headers: %s", response.headers)
            _logger.info("MPESA_TOKEN: Raw response: %s", response.text)
            
            if not response.text:
                _logger.error("MPESA_TOKEN: Empty response received")
                return False
                
            json_data = json.loads(response.text)
            if 'access_token' not in json_data:
                _logger.error("MPESA_TOKEN: No access token in response: %s", json_data)
                return False
                
            _logger.info("MPESA_TOKEN: Successfully obtained access token")
            return json_data["access_token"]
            
        except requests.exceptions.RequestException as e:
            _logger.error("MPESA_TOKEN: Request failed with error: %s", str(e))
            return False
        except json.JSONDecodeError as e:
            _logger.error("MPESA_TOKEN: Failed to parse JSON response: %s", str(e))
            return False
        except Exception as e:
            _logger.error("MPESA_TOKEN: Unexpected error: %s", str(e))
            return False

    def trigger_stk_push(self, provider, mobile_number, amount):
        _logger.info("MPESA_STK: Starting STK push for amount %s to number %s", amount, mobile_number)
        
        # Store initiating phone number
        _logger.info("MPESA_STK: Saving initiating phone number: %s", mobile_number)
        self.write({
            'mpesa_initiating_phone': mobile_number,
        })

        test_mode = (
            True
            if provider.state in ["test", "enabled"]
            else None if provider.state == "disabled" else False
        )
        
        # Change endpoint based on test_mode
        mpesa_endpoint = (
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            if test_mode
            else "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        )
        
        token = self._mpesa_get_access_token(
            provider.mpesa_online_consumer_key,
            provider.mpesa_online_consumer_secret,
            test_mode,
        )
        
        if not token:
            error_msg = "Failed to obtain valid access token"
            _logger.error("MPESA_STK: %s", error_msg)
            return {
                "payment_state": "error",
                "status": "error",
                "message": "Failed to authenticate with MPesa",
                "error_message": error_msg,
            }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        try:
            short_code = provider.mpesa_online_service_number
            pass_key = provider.mpesa_online_passkey
            
            time_stamp, password = self.get_timestamp_passkey(short_code, pass_key)
            
            payload = {
                "BusinessShortCode": short_code,
                "Password": password,
                "Timestamp": time_stamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(float(amount)),
                "PartyA": mobile_number,
                "PartyB": provider.mpesa_online_service_number,
                "PhoneNumber": mobile_number,
                "CallBackURL": provider.mpesa_online_callback_url,
                "AccountReference": self.reference,
                "TransactionDesc": "Product Purchase",
            }
            
            _logger.info("MPESA_STK: Sending request with payload: %s", payload)
            response = requests.post(
                mpesa_endpoint,
                headers=headers,
                json=payload,
                timeout=30,
            )
            
            _logger.info("MPESA_STK: Response status: %s", response.status_code)
            _logger.info("MPESA_STK: Response body: %s", response.text)
            
            if response.status_code != 200:
                error_msg = response.json().get("errorMessage", "Unknown error")
                _logger.error("MPESA_STK: Failed to send STK push: %s", error_msg)
                return {
                    "payment_state": "error",
                    "status": "error",
                    "message": "Failed to send STK push",
                    "error_message": error_msg,
                }
            
            checkout_request_id = response.json().get("CheckoutRequestID")
            self.mpesa_online_checkout_request_id = checkout_request_id
            self.mpesa_online_time_stamp = time_stamp
            self.mpesa_online_password = password
            
            # Query transaction status
            mpesa_query_url = (
                "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
                if test_mode
                else "https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query"
            )
            
            query_payload = {
                "BusinessShortCode": short_code,
                "Password": password,
                "Timestamp": time_stamp,
                "CheckoutRequestID": checkout_request_id,
            }
            
            timeout_duration = 30
            interval = 3
            start_time = time.time()
            state = "pending"
            error_msg = ""
            result_code = None
            
            while time.time() - start_time < timeout_duration:
                try:
                    _logger.info("MPESA_STK: Checking transaction status...")
                    
                    # Check if callback was already received
                    self.env.cr.execute("""
                        SELECT mpesa_receipt FROM payment_transaction 
                        WHERE id = %s AND mpesa_receipt IS NOT NULL
                    """, (self.id,))
                    has_callback = bool(self.env.cr.fetchone())
                    
                    if has_callback:
                        _logger.info("MPESA_STK: Callback already received, stopping status checks")
                        state = "done"
                        break

                    status_response = requests.post(
                        mpesa_query_url, 
                        json=query_payload, 
                        headers=headers, 
                        timeout=30
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        _logger.info("MPESA_STK: Status response: %s", status_data)
                        
                        result_code = status_data.get("ResultCode")
                        if result_code == "0":
                            state = "done"
                            break
                        elif result_code:  # If we got a result code but not 0
                            state = "error"
                            error_msg = self._get_mpesa_error_message(result_code)
                            break
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    _logger.error("MPESA_STK: Error checking status: %s", str(e))
            
            # Create logs
            self.create_mpesa_logs(
                payload,
                response.status_code,
                response.json(),
                checkout_request_id,
                self.id,
                result_code if state != "pending" else "",
                error_msg
            )
            
            if state == "done":
                return {
                    "payment_state": "done",
                    "status": "success",
                    "message": "Payment completed successfully",
                    "error_message": "",
                }
            elif state == "error":
                return {
                    "payment_state": "error",
                    "status": "error",
                    "message": "Payment failed",
                    "error_message": error_msg,
                }
            else:
                return {
                    "payment_state": "pending",
                    "status": "pending",
                    "message": "Waiting for payment confirmation",
                    "error_message": "",
                }
                
        except Exception as e:
            _logger.error("MPESA_STK: Unexpected error: %s", str(e))
            return {
                "payment_state": "error",
                "status": "error",
                "message": "System error occurred",
                "error_message": str(e),
            }

    def _get_mpesa_error_message(self, result_code):
        """Get human-readable error message for MPesa result codes"""
        error_messages = {
            "1032": "Transaction cancelled by user",
            "2001": "Wrong PIN entered",
            "1037": "Transaction timeout",
            "1": "Insufficient funds",
        }
        return error_messages.get(str(result_code), f"Transaction failed with code {result_code}")

    def query_transaction_status(self):
        for record in self.search([("mpesa_online_checkout_request_id", "!=", False)]):
            print(record)
            print(record.payment_method_id)
            provider_id = record.payment_method_id.provider_ids
            time_stamp, password = self.get_timestamp_passkey(
                provider_id.mpesa_online_service_number,
                provider_id.mpesa_online_consumer_secret,
            )
            query_data = {
                #     "BusinessShortCode": record.shortcode,
                "BusinessShortCode": provider_id.mpesa_online_service_number,
                "Password": record.mpesa_online_password,
                "Timestamp": record.mpesa_online_time_stamp,
                "CheckoutRequestID": record.mpesa_online_checkout_request_id,
            }
            test_mode = (
                True
                if provider_id.state in ["test", "enabled"]
                else None if provider_id.state == "disabled" else False
            )
            mpesa_endpoint = (
                "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            )
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer %s"
                % self._mpesa_get_access_token(
                    provider_id.mpesa_online_consumer_key,
                    provider_id.mpesa_online_consumer_secret,
                    test_mode,
                ),
            }
            response = requests.post(mpesa_endpoint, json=query_data, headers=headers)
            response_data = response.json()
            print(response_data)

    def _send_transaction_sms(self):
        """Send SMS notification for successful transaction"""
        _logger.info("SMS_NOTIFY: Starting SMS notification process for transaction %s", self.reference)
        
        sms_config = self.env['mpesa.sms.config'].search([('is_enabled', '=', True)], limit=1)
        if not sms_config:
            _logger.warning("SMS_NOTIFY: No enabled SMS configuration found")
            return False

        try:
            # Check for MPesa receipt in transaction
            has_mpesa_receipt = bool(self.mpesa_receipt)
            _logger.info("SMS_NOTIFY: Transaction has MPesa receipt: %s", has_mpesa_receipt)

            # Get phone number and template
            phone_number = self.mpesa_payment_phone or self.mpesa_initiating_phone
            if not phone_number:
                _logger.error("SMS_NOTIFY: No phone number available")
                return False

            # Format phone number
            phone_number = str(phone_number).replace('+', '').replace('254254', '254')
            if not phone_number.startswith('254'):
                phone_number = '254' + phone_number.lstrip('0')

            # Choose template based on whether we have MPesa receipt
            if has_mpesa_receipt:
                _logger.info("SMS_NOTIFY: Using configured template with receipt number")
                message = sms_config.sms_template.format(
                    amount="{:,.2f}".format(self.amount),
                    mpesa_ref=self.mpesa_receipt,
                    phone=phone_number,
                    purchase_id=self.reference
                )
            else:
                _logger.info("SMS_NOTIFY: Using basic template without receipt number")
                message = (
                    "Dear Customer, Your Transaction Confirmed! "
                    "Amount: KES {amount} "
                    "Purchase Reference:{purchase_id} "
                    "Thank you for shopping with us."
                ).format(
                    amount="{:,.2f}".format(self.amount),
                    purchase_id=self.reference
                )

            # Send SMS using client
            client = DibonSMSClient(sms_config.api_key)
            response = client.send_sms(
                sender=sms_config.sender_id,
                recipient=phone_number,
                message=message,
                ref_id=self.reference
            )

            _logger.info("SMS_NOTIFY: SMS API Response: %s", response)

            # Create SMS log
            _logger.info("SMS_NOTIFY: Creating SMS log entry...")
            sms_log_vals = {
                'name': response.get('msgId'),
                'sender_id': sms_config.id,
                'recipient': phone_number,
                'message': message,
                'status': 'success' if response.get('status') == 'SUCCESS' else 'failed',
                'cost': float(response.get('cost', '0').replace('KES ', '')),
                'reference': self.reference,
                'transaction_id': self.id,
            }
            _logger.info("SMS_NOTIFY: SMS log values: %s", sms_log_vals)
            
            sms_log = self.env['mpesa.sms.log'].create(sms_log_vals)
            _logger.info("SMS_NOTIFY: Successfully created SMS log with ID: %s", sms_log.id)

            # Update sender balance
            if response.get('balance'):
                _logger.info("SMS_NOTIFY: Updating sender balance to: %s", response['balance'])
                sms_config.update_balance(response['balance'])

            if response.get('error'):
                _logger.error("SMS_NOTIFY: Failed to send SMS: %s", response['error'])
                return False

            _logger.info("SMS_NOTIFY: Successfully sent SMS for transaction %s", self.reference)
            return True

        except Exception as e:
            _logger.error("SMS_NOTIFY: Unexpected error: %s", str(e))
            return False

    def create_mpesa_logs(self, payload, status_code, response_json, checkout_request_id, payment_transaction_id, result_code, error_msg):
        """Create MPesa transaction logs"""
        try:
            log_vals = {
                'name': str(payload),
                'status_code': status_code,
                'response': str(response_json),
                'checkout_request_id': checkout_request_id,
                'payment_transaction_id': payment_transaction_id,
                'result_code': result_code,
                'response_error': error_msg
            }
            self.env['mpesa.log'].sudo().create(log_vals)
            _logger.info("MPESA_LOG: Created log entry for checkout request ID: %s", checkout_request_id)
        except Exception as e:
            _logger.error("MPESA_LOG: Failed to create log entry: %s", str(e))
