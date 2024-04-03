from django.urls import path
from .views import RazorPay, CallbackRazorpay, QrCodePaymentView
urlpatterns = [

   path("razorpay/", RazorPay.as_view(), name="razorpay"),
   path("qrcode/", QrCodePaymentView.as_view(), name="qrcode"),
   path("callbackrazorpay/", CallbackRazorpay.as_view(), name="callbackrazorpay")
]