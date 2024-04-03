from rest_framework.permissions import BasePermission
import razorpay
from django.http import HttpResponse
from utils import get_env

key_id=get_env('RAZOR_PAY_KEY_ID')
key_secret=get_env('RAZOR_PAY_SECRET_KEY')
webhook_secret_key=get_env('WEBHOOK_SECRET_KEY')
client = razorpay.Client(auth=(key_id,key_secret))

class IsRazorpay(BasePermission):
    def has_permission(self, request, view):
      payment_data = request.headers
      if 'X-Razorpay-Signature' not in payment_data:
         return False
      signature = payment_data['X-Razorpay-Signature']
      if not client.utility.verify_webhook_signature(payment_data, signature, webhook_secret_key):
        return HttpResponse('Invalid signature')
      else:
         return True
