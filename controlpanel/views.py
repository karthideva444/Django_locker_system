# views.py
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from storage_locker.models import Customer
from storage_locker.serializers import CustomerSerializer

class CustomerListView(ListAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def list(self, request, *args, **kwargs):
        # Call the parent class's list method to get the default response
        response = super().list(request, *args, **kwargs)
        print(response.data)
        # Modify the response or add custom fields as needed
        # custom_data = {
        #     'custom_field': 'Custom Value',
        #     'another_field': 'Another Custom Value',
        # }

        # # Add the custom data to the response
        # response.data['custom_data'] = custom_data

        return Response(response.data)
