import requests
import json
import logging
from typing import Optional

_logger = logging.getLogger(__name__)

class DibonSMSClient:
    def __init__(self, api_key: str):
        self.endpoint = "http://sms.dibon.co.ke:8989/api/messaging/sendsms"
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"  # Fixed authorization header format
        }

    def send_sms(
        self,
        sender: str,
        recipient: str,
        message: str,
        ref_id: Optional[str] = None,
        link_id: Optional[str] = None,
        message_type: Optional[str] = None
    ) -> dict:
        try:
            # Format phone number to required format
            recipient = str(recipient).replace('+', '').replace('254254', '254')
            if not recipient.startswith('254'):
                recipient = '254' + recipient.lstrip('0')

            # Construct payload according to API specification
            payload = {
                "from": sender,  # Changed from partnerID to from
                "to": recipient,  # Changed from mobile to to
                "message": message
            }

            # Add optional parameters if provided
            if ref_id:
                payload["refId"] = ref_id
            if link_id:
                payload["linkId"] = link_id
            if message_type:
                payload["messageType"] = message_type

            _logger.info("SMS_CLIENT: Sending SMS request with payload: %s", {
                **payload,
                'from': sender  # Show sender ID in logs
            })
            _logger.debug("SMS_CLIENT: Using headers: %s", {
                **self.headers,
                'Authorization': 'Bearer ****'  # Hide API key in logs
            })

            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            _logger.info("SMS_CLIENT: Response status: %s", response.status_code)
            _logger.info("SMS_CLIENT: Response body: %s", response.text)

            if response.status_code != 200:
                _logger.error("SMS_CLIENT: Request failed with status %s", response.status_code)
                return {"error": f"Request failed with status {response.status_code}"}

            try:
                return response.json()
            except json.JSONDecodeError:
                return {"status": "success"} if response.status_code == 200 else {"error": "Invalid response"}

        except requests.exceptions.RequestException as e:
            _logger.error("SMS_CLIENT: Network error: %s", str(e))
            return {"error": f"Network error: {str(e)}"}
        except Exception as e:
            _logger.error("SMS_CLIENT: Unexpected error: %s", str(e))
            return {"error": f"Unexpected error: {str(e)}"}
