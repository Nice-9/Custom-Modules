import logging
from odoo import http
from .dibon_sms_client import DibonSMSClient

_logger = logging.getLogger(__name__)

class SMSController:
    @classmethod
    def send_transaction_sms(cls, env, transaction):
        """Send SMS notification for successful Mpesa transaction"""
        try:
            _logger.info("SMS_CONTROLLER: Starting SMS notification for transaction %s", 
                        transaction.reference)

            # Get SMS configuration
            sms_config = env['mpesa.sms.config'].search([('is_enabled', '=', True)], limit=1)
            if not sms_config:
                _logger.warning("SMS_CONTROLLER: No enabled SMS configuration found")
                return False

            # Get transaction details
            mpesa_receipt = transaction.mpesa_online_merchant_request_id
            phone_number = transaction.partner_phone
            
            _logger.info("SMS_CONTROLLER: Transaction details - Receipt: %s, Phone: %s", 
                        mpesa_receipt, phone_number)

            if not mpesa_receipt or not phone_number:
                _logger.error("SMS_CONTROLLER: Missing required transaction details")
                return False

            client = DibonSMSClient(sms_config.api_key)

            # Format message
            try:
                message = sms_config.sms_template.format(
                    amount=transaction.amount,
                    mpesa_ref=mpesa_receipt,
                    phone=phone_number,
                    purchase_id=transaction.reference
                )
                _logger.info("SMS_CONTROLLER: Formatted message: %s", message)
            except KeyError as ke:
                _logger.error("SMS_CONTROLLER: Message template error - missing key: %s", str(ke))
                return False
            except Exception as e:
                _logger.error("SMS_CONTROLLER: Message formatting error: %s", str(e))
                return False

            # Send SMS
            response = client.send_sms(
                sender=sms_config.sender_id,
                recipient=phone_number,
                message=message,
                ref_id=transaction.reference
            )

            if response.get('error'):
                _logger.error("SMS_CONTROLLER: Failed to send SMS: %s", response['error'])
                return False

            _logger.info("SMS_CONTROLLER: SMS sent successfully: %s", response)
            return True

        except Exception as e:
            _logger.error("SMS_CONTROLLER: Unexpected error: %s", str(e))
            return False
