# payment/views.py
import requests
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from .models import Payment
from django.shortcuts import render

class PhonePePaymentView(APIView):
    def post(self, request, *args, **kwargs):
        # Fetch payment details from the request
        amount = request.data.get('amount')  # Assuming the amount is passed in the request

        # Prepare the data for PhonePe API request
        payload = {
            'merchant_key': settings.PHONEPE_MERCHANT_KEY,
            'amount': amount,
            'transaction_type': 'SALE',
            'currency': 'INR',
            'order_id': 'order_' + str(request.user.id),  # Unique order ID
            'callback_url': 'https://yourwebsite.com/payment/callback/',  # PhonePe will call this URL
            'redirect_url': 'https://yourwebsite.com/payment/success/',  # After payment success, redirect here
        }

        # Make the API request to PhonePe to initiate the payment
        response = requests.post(settings.PHONEPE_API_URL, data=payload)
        response_data = response.json()

        if response_data.get('status') == 'success':
            # Save the payment record
            payment = Payment.objects.create(
                user=request.user,
                amount=amount,
                payment_status='pending',
                transaction_id=response_data.get('transaction_id'),
                payment_method='phonepe'
            )

            # Redirect user to PhonePe's payment page
            return JsonResponse({'payment_url': response_data.get('payment_url')})
        else:
            return JsonResponse({'error': 'Payment initiation failed'}, status=400)
# payment/views.py
from django.http import HttpResponse

class PhonePeCallbackView(APIView):
    def post(self, request, *args, **kwargs):
        # PhonePe will send details of the transaction here
        transaction_data = request.data
        
        # Check the status of the payment
        transaction_id = transaction_data.get('transaction_id')
        status = transaction_data.get('status')
        
        # Update the payment status in the database
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            if status == 'success':
                payment.payment_status = 'completed'
                # Reduce stock for each product in the order
                order = payment.order
                for order_product in order.products.all():
                    order_product.reduce_stock(order_product.quantity)  # Reduce stock
                
                payment.save()
            else:
                payment.payment_status = 'failed'
            payment.save()
            
            # Send a response to PhonePe
            return HttpResponse(status=200)
        except Payment.DoesNotExist:
            return HttpResponse('Payment record not found', status=404)
