from rest_framework.views import APIView
from rest_framework.response import Response
from os.path import abspath, dirname
from .payment_utils import build_razorpay_response
import os, requests
from rest_framework import status
from logging import LoggerAdapter
from users.utils import get_logger
from utils import get_env

LOG_DIR = str(abspath(dirname(dirname(__file__)
                              ))) + os.sep


LOGGER_NAME = "RazorPay"
LOG_EXTRAS = {"process_name": "RazorPay Payment Process"}
LOGGER = LoggerAdapter(
    get_logger(logger_name=LOGGER_NAME, log_file_path=LOG_DIR), extra=LOG_EXTRAS
)
key_id=get_env('RAZOR_PAY_KEY_ID')
key_secret=get_env('RAZOR_PAY_SECRET_KEY')
secret_key = get_env("JWT_SECRET_KEY")
RAZOR_PAY_PAYMENT_LINK=get_env('RAZOR_PAY_PAYMENT_LINK')
RAZOR_PAY_QR_LINK=get_env('RAZOR_PAY_QR_LINK')
class RazorPay(APIView):
  
  def post(self, request):
    try:
      data = request.data
      headers = {"Content-type": "application/json"}
      response = requests.post(RAZOR_PAY_PAYMENT_LINK,auth=(key_id, key_secret), headers=headers, json=data)
      # Check the response
      if response.status_code == 200:
        response = build_razorpay_response(response.json())
        return Response(response,status=status.HTTP_200_OK)
      else:
        LOGGER.info('Request failed with status code {} with an error {}'.format(response.status_code, response.text))
        return Response(response,status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
      response_data = {"msg": "Internal Server Error", "code": 500}
      LOGGER.error("Exception Occured: {}".format(str(e)))
      return Response(response_data,status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class QrCodePaymentView(APIView):

  def post(self, request):
    try:
      data = request.data
      headers = {"Content-type": "application/json"}
      response = requests.post(RAZOR_PAY_QR_LINK,auth=(key_id, key_secret), headers=headers, json=data)
      # Check the response
      if response.status_code == 200:
        response = response.json()
        return Response(response,status=status.HTTP_200_OK)
      else:
        LOGGER.info('Request failed with status code {} with an error {}'.format(response.status_code, response.text))
        return Response(response,status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
      response_data = {"msg": "Internal Server Error", "code": 500}
      LOGGER.error("Exception Occured: {}".format(str(e)))
      return Response(response_data,status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class CallbackRazorpay(APIView):
  def post(self, request):
    try:
      data = request.data
      LOGGER.info(data)
      return Response(data)
    except Exception as e:
      return Response(e)