# -*- coding: utf-8 -*-

import datetime
import json
import logging

from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

import odoo
from odoo import _, fields, http

_logger = logging.getLogger(__name__)


class LipaNaMpesa(http.Controller):
    """Mpesa online routes for callback url and for submitting payment form data"""

    @http.route(
        "/mpesa_express", type="http", auth="public", methods=["POST"], csrf=False
    )
    def index(self, **kw):
        """Lipa na MPESA Online Callback URL"""
        try:
            # Get JSON data from request
            data = None
            if request.httprequest.data:
                try:
                    data = json.loads(request.httprequest.data.decode('utf-8'))
                except json.JSONDecodeError:
                    data = kw
            else:
                data = kw

            _logger.info("MPESA_CALLBACK: Received data: %s", data)

            if 'Body' in data and 'stkCallback' in data['Body']:
                callback_data = data['Body']['stkCallback']
                metadata = callback_data.get('CallbackMetadata', {}).get('Item', [])
                
                # Extract callback data
                mpesa_data = {}
                for item in metadata:
                    name = item.get('Name')
                    value = item.get('Value')
                    if name == 'MpesaReceiptNumber':
                        mpesa_data['receipt'] = value
                    elif name == 'PhoneNumber':
                        mpesa_data['phone'] = str(value)
                    elif name == 'Amount':
                        mpesa_data['amount'] = value

                _logger.info("MPESA_CALLBACK: Extracted data: %s", mpesa_data)
                
                if mpesa_data:
                    checkout_request_id = callback_data.get('CheckoutRequestID')
                    tx = request.env['payment.transaction'].sudo().search([
                        ('mpesa_online_checkout_request_id', '=', checkout_request_id)
                    ], limit=1)

                    if tx and callback_data.get('ResultCode') == 0:
                        # First update transaction with callback data
                        tx.write({
                            'mpesa_payment_phone': mpesa_data.get('phone'),
                            'mpesa_receipt': mpesa_data.get('receipt')
                        })
                        
                        # Then send SMS
                        tx.sudo()._send_transaction_sms()
                        
                        # Finally mark as done
                        tx._set_done()

            return http.Response(json.dumps({'status': 'success'}), status=200)

        except Exception as e:
            _logger.error("MPESA_CALLBACK: Error: %s", str(e))
            return http.Response(json.dumps({'error': str(e)}), status=500)

    @http.route(
        "/payment/mpesa_online",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def lipa_na_mpesa(self, **post):
        """To handle HTTP Post from the lipa na mpesa form"""

        user = post.get("mpesa_phone_number")
        msg = _("MPESA_ONLINE: Receiving payment form data for transaction ref")
        msg += "<%s>" % post.get("reference", "")
        msg += " for <%s>" % user
        _logger.info(msg)
        if not http.request.session.get("sale_order_id") and http.request.session.get(
            "sale_last_order_id"
        ):
            http.request.session.update(
                sale_order_id=http.request.session.get("sale_last_order_id")
            )
        tx_id = request.session.get("__website_sale_last_tx_id", False)
        if tx_id:
            post.update(tx_id=tx_id)

        if (
            http.request.env["payment.transaction"]
            .sudo()
            .form_feedback(post, "mpesa_online")
        ):
            msg = _("MPESA_ONLINE: Completed sending payment request to customer")
            msg += " <%s>" % user
            _logger.info(msg)
            msg = _("MPESA_ONLINE: redirecting back to Odoo payment process.")
            _logger.info(msg)
            return http.request.redirect(post.pop("return_url"))
        return http.request.redirect("/shop/payment")

    @http.route('/payment/mpesa_online/submit', type='http', auth='public', website=True, csrf=False)
    def submit_manual_payment(self, **post):
        """Handle manual MPesa payment submission"""
        _logger.info("MPESA_MANUAL: Received payment submission: %s", post)
        
        if not post.get('mpesa_receipt') or not post.get('mpesa_phone_number'):
            return request.redirect('/shop/payment')

        # Create payment transaction
        tx_sudo = request.env['payment.transaction'].sudo().create({
            'reference': post.get('reference'),
            'amount': float(post.get('amount')),
            'currency_id': int(post.get('currency_id')),
            'partner_id': int(post.get('partner_id')),
            'provider_id': int(post.get('provider_id')),
            'manual_payment': True,
            'mpesa_receipt': post.get('mpesa_receipt'),
            'mpesa_phone': post.get('mpesa_phone_number'),
            'state': 'pending'
        })

        # Process the payment
        if tx_sudo:
            tx_sudo._process_manual_payment({
                'mpesa_receipt': post.get('mpesa_receipt'),
                'mpesa_phone_number': post.get('mpesa_phone_number'),
                'manual_payment': True
            })
            
            return request.redirect('/payment/status')
        
        return request.redirect('/shop/payment')

    @http.route('/payment/mpesa_online/submit', type='json', auth='public', website=True, csrf=False)
    def mpesa_submit_payment(self, **post):
        """Handle MPesa payment submission"""
        _logger.info("MPESA_SUBMIT: Payment submission received: %s", post)
        
        try:
            # Create payment transaction
            tx_sudo = request.env['payment.transaction'].sudo().create({
                'reference': post.get('reference'),
                'amount': float(post.get('amount')),
                'currency_id': int(post.get('currency_id')),
                'partner_id': int(post.get('partner_id')),
                'provider_id': int(post.get('acquirer_id')),
                'manual_payment': True,
                'mpesa_receipt': post.get('mpesa_receipt'),
                'mpesa_phone': post.get('mpesa_phone_number'),
                'state': 'pending'
            })

            # Process the payment
            if tx_sudo:
                tx_sudo._process_manual_payment({
                    'mpesa_receipt': post.get('mpesa_receipt'),
                    'mpesa_phone_number': post.get('mpesa_phone_number'),
                    'manual_payment': True
                })
                
                return {'success': True}
            
            return {'success': False, 'error': 'Could not create transaction'}
            
        except Exception as e:
            _logger.error("MPESA_SUBMIT: Error processing payment: %s", str(e))
            return {'success': False, 'error': str(e)}


class PosMpesaController(http.Controller):
    _callback_url = "/payment/mpesa/callback/"

    @http.route(
        ["/payment/mpesa/callback/"],
        type="json",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def mpesa_return(self, **post):
        """
        :param data:
        {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "20429-25587672-1",
                    "CheckoutRequestID": "ws_CO_020220221007215649",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {
                                "Name": "Amount",
                                "Value": 1.0
                            },
                            {
                                "Name": "MpesaReceiptNumber",
                                "Value": "QB25IC9R1D"
                            },
                            {
                                "Name": "Balance"
                            },
                            {
                                "Name": "TransactionDate",
                                "Value": 20220202100931
                            },
                            {
                                "Name": "PhoneNumber",
                                "Value": 254727834462
                            }
                        ]
                    }
                }
            }
        }
        :return:
        """
        params = request.jsonrequest or {}
        _logger.info("Call Back request received from mpesa (json) :\n%s", params)
        if params:
            data = params["Body"]["stkCallback"]
            merchant_request_id = data.get("MerchantRequestID")
            checkout_request_id = data.get("CheckoutRequestID")
            res_code = data.get("ResultCode")
            amount = 0
            _logger.info("Data:\n%s", data)
            _logger.info("merchant_request_id:\n%s", merchant_request_id)
            _logger.info("checkout_request_id:\n%s", checkout_request_id)
            _logger.info("res_code:\n%s", res_code)
            if checkout_request_id:
                tx = self.find_or_create_payment(
                    merchant_request_id, checkout_request_id
                )
                _logger.info(tx)
                if not tx or len(tx) > 1:
                    error_msg = (
                        _("Mpesa: received data for CheckoutRequestID %s")
                        % checkout_request_id
                    )
                    if not tx:
                        error_msg += _("; no order found")
                    else:
                        error_msg += _("; multiple order found")
                    _logger.info(error_msg)
                    raise ValidationError(error_msg)
                (
                    receipt_number,
                    receipt_date,
                    phone_number,
                    amount,
                    state,
                    result_description,
                ) = self.extract_callback_metadata(
                    data.get("CallbackMetadata", {}),
                    data.get("ResultCode"),
                    data.get("ResultDesc"),
                )
                tx.write(
                    {
                        "receipt_number": receipt_number,
                        "receipt_date": receipt_date,
                        "amount": amount,
                        "phone_number": phone_number,
                        "result_description": result_description,
                        "state": state,
                        # 'is_pos_request': False,
                    }
                )
            txn = (
                request.env["pos.mpesa.payment"]
                .sudo()
                .search(
                    [
                        ("merchant_request_id", "=", merchant_request_id),
                        ("checkout_request_id", "=", checkout_request_id),
                        # ("date_validate", "<=", datetime.datetime.now()),
                    ],
                    limit=1,
                    order="id desc",
                )
            )
            _logger.info(txn)
            _logger.info(_("MPESA PAYMENT: Data successfully stored in the system"))
        return "Success"

    def extract_callback_metadata(
        self, callback_metadata, result_code, result_description
    ):
        receipt_number = None
        receipt_date = None
        phone_number = None
        amount = 0

        for item in callback_metadata.get("Item", []):
            name = item.get("Name")
            value = item.get("Value")
            if name == "TransactionDate":
                receipt_date = datetime.datetime.strptime(
                    str(value), "%Y%m%d%H%M%S"
                ).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            elif name == "Amount":
                amount = value
            elif name == "MpesaReceiptNumber":
                receipt_number = value
            elif name == "PhoneNumber":
                phone_number = value

        state = "done" if result_code == 0 else "cancel"

        return (
            receipt_number,
            receipt_date,
            phone_number,
            amount,
            state,
            result_description,
        )

    def find_or_create_payment(self, merchant_request_id, checkout_request_id):
        pos_mpesa_payment = (
            request.env["pos.mpesa.payment"]
            .sudo()
            .search(
                [
                    "|",
                    ("merchant_request_id", "=", merchant_request_id),
                    ("checkout_request_id", "=", checkout_request_id),
                ],
                limit=1,
            )
        )
        if not pos_mpesa_payment:
            _logger.info(
                _("Mpesa: received data with new reference (%s)") % checkout_request_id
            )
            values = {
                "checkout_request_id": checkout_request_id,
                "merchant_request_id": merchant_request_id,
            }
            pos_mpesa_payment = request.env["pos.mpesa.payment"].create(values)
            _logger.info(pos_mpesa_payment)
        return pos_mpesa_payment


class MpesaCashPayment(http.Controller):
    _return_url = "/payment/mpesa_online/return"

    @http.route(
        "/v1/payment_notification",
        type="json",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def mpesa_notification_json_post(self, **kwargs):
        _logger.info("data: transaction %s", str(json.loads(request.httprequest.data)))
        values = {}
        not_accepted = "Not Accepted"
        post = json.loads(request.httprequest.data)
        if not post:
            _logger.info("Data is not getting!")
            result = {"ResultCode": 1, "ResultDesc": not_accepted}
            return json.dumps(result)
        values.update(
            {
                "ref": post.get("BusinessShortCode"),
                "datas": json.dumps(post),
                "transaction_type": post.get("TransactionType"),
                "trans_id": post.get("TransID"),
                "trans_time": post.get("TransTime"),
                "amount": float(post.get("TransAmount", 0.00)),
                "business_shortcode": post.get("BusinessShortCode"),
                "bill_ref_number": post.get("BillRefNumber"),
                "invoice_number": post.get("InvoiceNumber"),
                "org_account_balance": post.get("OrgAccountBalance"),
                "third_party_transid": post.get("ThirdPartyTransID"),
                "msisdn": post.get("MSISDN"),
                "first_name": post.get("FirstName"),
                "middle_name": post.get("MiddleName"),
                "last_name": post.get("LastName"),
            }
        )
        date = fields.Date.to_string(datetime.date.today())
        values.update({"payment_date": date})
        dbname = post.get("db", "")
        if not dbname:
            _logger.warning("Database name is not found!")
            result = {"ResultCode": 1, "ResultDesc": not_accepted}
            return json.dumps(result)
        odoo.registry(str(dbname))
        try:
            request.env["pos.mpesa.payment"].sudo().create(values)
        except Exception as e:
            if not str(e).isnumeric():
                return json.dumps(
                    {"ResultCode": 1, "ResultDesc": not_accepted, "Error": str(e)}
                )
        result = {"ResultCode": 0, "ResultDesc": "Accepted"}
        return json.dumps(result)

    @http.route(_return_url, type="json", auth="public")
    def mpesa_return_url(self, **data):
        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            ._handle_notification_data("mpesa_online", data)
        )


from odoo import http, _
from odoo.http import request
from .sms_controller import SMSController
import json
import logging

_logger = logging.getLogger(__name__)

class MpesaPayment(http.Controller):
    @http.route('/mpesa/confirmation', type='json', auth='public', csrf=False, methods=['POST'])
    def mpesa_confirmation(self, **kwargs):
        try:
            # Get the JSON data
            data = json.loads(request.httprequest.data)
            _logger.info('Mpesa confirmation received: %s', data)

            # Process the transaction
            if data.get('ResultCode') == '0':  # Successful transaction
                # Create or update transaction record
                transaction = request.env['mpesa.transaction'].sudo().create({
                    'mpesa_ref': data.get('TransactionID'),
                    'phone_number': data.get('MSISDN'),
                    'amount': float(data.get('TransAmount')),
                    'status': 'completed',
                    # Add other relevant fields
                })

                # Send SMS notification
                if transaction:
                    try:
                        sms_sent = SMSController.send_transaction_sms(request.env, transaction)
                        if sms_sent:
                            _logger.info('SMS notification sent successfully for transaction %s', 
                                       transaction.mpesa_ref)
                        else:
                            _logger.warning('Failed to send SMS notification for transaction %s', 
                                          transaction.mpesa_ref)
                    except Exception as e:
                        _logger.error('Error sending SMS: %s', str(e))

                return {
                    'ResultCode': 0,
                    'ResultDesc': 'Confirmation received successfully'
                }
            else:
                _logger.error('Failed transaction: %s', data.get('ResultDesc'))
                return {
                    'ResultCode': 1,
                    'ResultDesc': 'Transaction failed'
                }

        except Exception as e:
            _logger.error('Error processing confirmation: %s', str(e))
            return {
                'ResultCode': 1,
                'ResultDesc': 'Error processing confirmation'
            }

    @http.route('/mpesa/validation', type='json', auth='public', csrf=False, methods=['POST'])
    def mpesa_validation(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            _logger.info('Mpesa validation received: %s', data)
            
            return {
                'ResultCode': 0,
                'ResultDesc': 'Validation successful'
            }
            
        except Exception as e:
            _logger.error('Validation error: %s', str(e))
            return {
                'ResultCode': 1,
                'ResultDesc': 'Validation failed'
            }

    @http.route('/mpesa/timeout', type='json', auth='public', csrf=False, methods=['POST'])  # Changed from method to methods
    def mpesa_timeout(self, **kwargs):
        _logger.warning('Mpesa timeout received: %s', kwargs)
        return {
            'ResultCode': 0,
            'ResultDesc': 'Timeout received'
        }


class MpesaController(http.Controller):
    @http.route('/mpesa/c2b', type='http', auth='public', methods=['POST'], csrf=False)
    def send_c2b(self, **post):
        try:
            # Get JSON data from request
            if request.httprequest.data:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            else:
                data = post
            
            _logger.info("C2B Request received: %s", data)
            # Rest of your code  # Changed from method to methods
            
        except Exception as e:
            _logger.error("C2B Error processing request: %s", str(e))
            return Response(
                json.dumps({'error': str(e)}),
                status=400,
                content_type='application/json'
            )

    @http.route('/mpesa_express', type='http', auth='public', methods=['POST'], csrf=False)
    def mpesa_callback(self, **post):
        try:
            # Get JSON data from request
            data = None
            if request.httprequest.data:
                try:
                    data = json.loads(request.httprequest.data.decode('utf-8'))
                    _logger.info("MPESA_CALLBACK: Received raw data: %s", data)
                except json.JSONDecodeError as e:
                    _logger.error("MPESA_CALLBACK: JSON decode error: %s", str(e))
                    data = post
            else:
                data = post

            if 'Body' in data and 'stkCallback' in data['Body']:
                callback_data = data['Body']['stkCallback']
                _logger.info("MPESA_CALLBACK: Processing STK callback: %s", callback_data)

                # Extract callback data
                checkout_request_id = callback_data.get('CheckoutRequestID')
                result_code = callback_data.get('ResultCode')
                result_desc = callback_data.get('ResultDesc')
                metadata = callback_data.get('CallbackMetadata', {}).get('Item', [])

                # Find transaction
                tx = request.env['payment.transaction'].sudo().search([
                    ('mpesa_online_checkout_request_id', '=', checkout_request_id)
                ], limit=1)

                if not tx:
                    _logger.error("MPESA_CALLBACK: No transaction found for checkout_request_id: %s", 
                                checkout_request_id)
                    return {'status': 'error', 'message': 'Transaction not found'}

                # Extract metadata
                mpesa_data = {}
                for item in metadata:
                    name = item.get('Name')
                    value = item.get('Value')
                    if name == 'MpesaReceiptNumber':
                        mpesa_data['receipt'] = value
                    elif name == 'PhoneNumber':
                        mpesa_data['phone'] = str(value)
                    elif name == 'Amount':
                        mpesa_data['amount'] = value

                _logger.info("MPESA_CALLBACK: Extracted data: %s", mpesa_data)

                # Update transaction
                if result_code == 0 and mpesa_data:
                    _logger.info("MPESA_CALLBACK: Updating transaction %s with data", tx.reference)
                    tx.write({
                        'mpesa_payment_phone': mpesa_data.get('phone'),
                        'mpesa_receipt': mpesa_data.get('receipt'),
                        'state': 'done'
                    })
                    
                    # Send SMS with receipt number
                    tx._send_transaction_sms()
                    _logger.info("MPESA_CALLBACK: Transaction processed successfully")
                else:
                    _logger.warning("MPESA_CALLBACK: Transaction failed with code %s: %s", 
                                  result_code, result_desc)
                    tx.write({'state': 'error'})

            return http.Response(json.dumps({'status': 'success'}), status=200)

        except Exception as e:
            _logger.error("MPESA_CALLBACK: Error processing callback: %s", str(e))
            return http.Response(json.dumps({'error': str(e)}), status=500)
