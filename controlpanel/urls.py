from django.urls import path
from .views import CustomerListView

urlpatterns = [
    # Your other URL patterns
    path('customer', CustomerListView.as_view(), name='your_data_api'),
]
