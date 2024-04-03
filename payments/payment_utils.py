import requests
import json
import time, uuid
from utils import get_env
from django.urls import reverse
import datetime
import pytz
import base64, hashlib


phonepe_paylink=get_env("PHONEPE_PAYLINK_URL")
payment_method = get_env("PAYMENT_METHOD")
internal_url = get_env("INTERNAL_API_ENDPOINT")
saltkey=get_env("SALT_KEY")
callback_url = get_env("CALLBACK_URL")
merchant_id = get_env("MERCHANT_ID")
redirect_url = get_env("REDIRECT_URL")
def  unix_timestamp():
  kolkata_timezone = pytz.timezone('Asia/Kolkata')
  current_time = datetime.datetime.now(kolkata_timezone)
  new_time = current_time + datetime.timedelta(minutes=16)
  expiry_by = int(new_time.timestamp())
  return expiry_by

def make_base64(json_obj):
    json_str = json.dumps(json_obj, separators=(",", ":"))  # compact encoding
    return base64.urlsafe_b64encode(bytes(json_str, "utf-8")).decode("utf-8")

def make_hash(input_str):
    m = hashlib.sha256()
    m.update(input_str.encode())
    return m.hexdigest()

def decode_base64(encoded_response):
  response = base64.b64decode(encoded_response['response']).decode("utf-8")
  response = json.loads(response)
  return response

def call_internal_api(request, data, reason, reference_id_type):
  if payment_method == 'razorpay':
    data['notes'] = {
      'payment_method':"RazorPay",
      'payment_type':'UPI',
      'reference_id_type':reference_id_type,
      'reason':reason,
      'reference_id':data['reference_id'],
      'booked_duration':data['booked_duration']
      }
    data['callback'] = internal_url + '/api/callback/'
    payload = build_razorpay_payload(data)
    url  = internal_url + reverse('razorpay')
    token = request.headers.get('Authorization')
    headers = {"Content-type": "application/json", 'Authorization': token}
    response = requests.post(url,data=payload, headers=headers).json()
    return payload, response
  elif payment_method == 'phonepeV1':
    payload, response = phonepe_payment_link(request,data,reason,reference_id_type)
    return payload, response
    

def build_razorpay_payload(data):
  payload = {
  "upi_link": "true",
  "amount": int(data['amount']),
  "currency": "INR",
  "expire_by": unix_timestamp(),
  "reference_id": data['reference_id'],
  "description": "Payment for policy no #23456",
  "customer": {
    "contact": str(data["contact"]),
    "booked_duration": data["booked_duration"],
  },
  "notify": {
    "sms": False,
    "email": False
  },
  "reminder_enable": True,
  "notes": data['notes'],
  "callback_url":data['callback'],
  "callback_method": "get"
}
  return json.dumps(payload)

def build_razorpay_response(data):
    return {
        'amount': data.get('amount'),
        'currency': data.get('currency'),
        'reference_id': data.get('reference_id'),
        'customer': data.get('customer'),
        'id': data.get('id'),
        'notes': data.get('notes'),
        'short_url': data.get('short_url'),
        'status': data.get('status'),
        'expire_by': data.get('expire_by'),
    }

def call_qr_code_api(request, data):
  payload = {
  "type": "upi_qr",
  "name": "Popoutbox QR Code",
  "usage": "single_use",
  "fixed_amount": True,
  "payment_amount": int(data['amount']),
  "description": "QrCode Payment",
  "customer_id": data['reference_id'],
  "close_by": unix_timestamp(),
  "notes":{
      'payment_method':"RazorPay",
      'payment_type':'QR Code',
      'reference_id':data['reference_id'],
      'booked_duration':data['booked_duration']
      }
}
  url  = internal_url + reverse('qrcode')
  token = request.headers.get('Authorization')
  payload =json.dumps(payload)
  headers = {"Content-type": "application/json", 'Authorization': token}
  response = requests.post(url,data=payload, headers=headers).json()
  return payload, response



def phonepe_payment_link(request, data, reason, reference_id_type):
  # payload ={
  #   "merchantId":merchant_id,
  #   "transactionId":data['reference_id'],
  #   "merchantOrderId":f"booking #{data['reference_id']}",
  #   "amount":int(data['amount']),
  #   "mobileNumber":str(data["contact"]),
  #   "message":reference_id_type,
  #   "expiresIn":300,
  #   "shortName":reason,
  #   "subMerchantId":data['reference_id'] 
  #   }
  payload ={
  "merchantId": merchant_id,
  "merchantTransactionId": data['reference_id'],
  "merchantUserId": "MUID123",
  "amount": int(data['amount']),
  "redirectUrl": redirect_url,
  "redirectMode": "REDIRECT",
  "callbackUrl": callback_url,
  "mobileNumber": str(data["contact"]),
  "paymentInstrument": {
    "type": "PAY_PAGE"
  }
}
  base64_payload = make_base64(payload)
  verification_str = base64_payload + "/pg/v1/pay" + saltkey
  X_VERIFY = make_hash(verification_str) + "###" + '1'
  payloads = {"request": base64_payload}
  headers = {
  "accept": "application/json",
  "Content-Type" : "application/json" ,
  "X-VERIFY" : X_VERIFY ,
  # "X-CALLBACK-URL" : callback_url ,
  # "X-CALL-MODE ": "POST" 
  }
  response = requests.post(phonepe_paylink, json=payloads, headers=headers)
  print("********************************")
  print(response.text)
  return payload, response.json()