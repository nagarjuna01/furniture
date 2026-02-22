from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from partisoproduct.models import MvpQuoteRequest
from partisoproduct.serializers.quote_serializers import HybridQuoteRequestSerializer

class MvpQuoteRequestViewSet(viewsets.ModelViewSet):
    queryset = MvpQuoteRequest.objects.all()
    serializer_class = HybridQuoteRequestSerializer

    @action(detail=False, methods=['post'], url_path='calculate_quote')
    def calculate_quote(self, request):
        """
        Calculates a quote based on the provided product and material data.
        Returns the calculated quote breakdown without saving it to the database.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                validated_data = serializer.validated_data
                
                # Assume your `calculate_price_service` returns a Python dictionary
                # or a model object. For this example, we'll assume it returns a
                # dictionary with a 'products' key containing a list of model objects.
                calculated_data_from_service = self.calculate_price_service(validated_data)
                
                # We need to serialize the product objects before returning.
                # This is the key to fixing the TypeError.
                serialized_products = ProductSerializer(
                    calculated_data_from_service['products'],
                    many=True
                ).data
                
                # Now, build a clean, serializable dictionary for the final response
                final_response_data = {
                    "customer_name": calculated_data_from_service['customer_name'],
                    "products": serialized_products,
                    "total_price": calculated_data_from_service['total_price']
                }
                
                return Response(final_response_data, status=status.HTTP_200_OK)

            except Exception as e:
                # This will now catch the error, log it, and send a clean 400 to the client
                print(f"Error during quote calculation: {e}")
                return Response({"error": "An unexpected error occurred during calculation. Please check server logs."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # You would need to define your `calculate_price_service` function,
    # ensuring it returns a dictionary with model instances or raw data.
    def calculate_price_service(self, validated_data):
        # Your complex business logic here...
        # For this example, we return a dictionary that matches the expected output.
        products = validated_data.get('products', [])
        
        # This is a placeholder. You would have your logic to get actual data.
        mock_product_objects = [
            {
                "id": p['modular_product'],
                "name": f"Product {p['modular_product']}",
                "price": 1000.00 * p['quantity']
            } for p in products
        ]
        
        return {
            "customer_name": validated_data.get('customer_name'),
            "products": mock_product_objects, # <-- This must be a list of dictionaries, not model instances
            "total_price": 5000.00
        }