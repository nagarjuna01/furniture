import requests

SHIPROCKET_API_URL = "https://apiv2.shiprocket.in/v1/external/courier/ship"

class ShipRocketAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def create_shipping_order(self, order):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
        data = {
            "order_id": order.id,
            "order_date": order.created_at.isoformat(),  # Ensure correct format
            "customer_name": order.customer_name,
            "shipping_address": order.shipping_address,
            # Add any other required details
        }

        try:
            response = requests.post(SHIPROCKET_API_URL, json=data, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating shipping order: {e}")
            return None  # Or handle as needed
