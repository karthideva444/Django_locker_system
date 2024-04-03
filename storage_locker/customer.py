from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from .models import Customer, Book,BizLkr, SecurityPin, BizLocation
from .serializers import CustomerSerializer, BookSerializer, SecurityPinSerializer
from logging import LoggerAdapter
from users.utils import get_logger
from .locker_utils import make_hash,send_response,response_builder
from os.path import abspath, dirname
import os

LOG_DIR = str(abspath(dirname(dirname(__file__)))) + os.sep
LOGGER_NAME = "Locker"
LOG_EXTRAS = {"process_name": "Customer Authentication"}
LOGGER = LoggerAdapter(
    get_logger(logger_name=LOGGER_NAME, log_file_path=LOG_DIR), extra=LOG_EXTRAS
)

class CheckCustomerView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        # Check if the customer exists in the table
        try:
            customer_name = request.data.get("customer_name","")   
            phone_number = request.data.get("phone_number",None)
            if (phone_number is None) or (len(str(phone_number)) <= 0) or (
            not str(phone_number).isdigit()) or (len(str(phone_number)) < 10):

                response = response_builder("Invalid Phone Number",{},'failed',400)
                return send_response(response, LOGGER)
            if len(str(phone_number)) > 0 and len(str(phone_number)) > 10:
                phone_number = int(str(phone_number)[-10:])
            try:
                customer = Customer.objects.get(
                    prim_no=phone_number,
                )
                if customer.name != customer_name and len(customer_name) > 0:
                    customer.name = customer_name
                    customer.save()
                serializer = CustomerSerializer(customer)
                cus_id = serializer.data["id"]
                try:
                    book = Book.objects.filter(cust_id=cus_id,active_boo = 1)
                    serialized_books = BookSerializer(book, many=True).data
                    if serialized_books:
                        book_data = []
                        for serialized_book in serialized_books:
                            biz_lkr_id = serialized_book['biz_lkr'] 
                            biz_lkr = BizLkr.objects.get(pk=biz_lkr_id)
                            loc_ins = BizLocation.objects.get(location_id=serialized_book['location_id'],
                                     biz_id=serialized_book['biz'])
                            biz_id = '{}-{}'.format(serialized_book['biz'], serialized_book['location_id'])
                            data = {
                            "book_id": serialized_book['id'],
                            'locker_no': biz_lkr.lock_no,
                            'biz':biz_id,
                            "loc_name": loc_ins.loc_name,
                            }
                            book_data.append(data)
                        data = {
                            "booked": True,
                            'booking_count': len(serialized_books),
                            "customer_id": cus_id,
                            "booking_info": book_data
                        }
                        response = response_builder(f"Locker Already booked by the customer id: {str(cus_id)}",
                                                    data,"success",200)
                        return send_response(response, LOGGER)
                    else:
                        data = {"booked": False, "customer_id": cus_id, 'booking_count':0, "booking_info":[]}
                        response = response_builder(f"Locker is not Booked by the customer id: {str(cus_id)}",
                                                    data,"success",200)
                        return send_response(response, LOGGER)
                except Book.DoesNotExist:
                    data = {"booked": False, "customer_id": cus_id, "booking_count":0,"booking_info":[]}
                    response = response_builder(f"Locker is not Booked by the customer id: {str(cus_id)}",
                                                data,"success",200)
                    return send_response(response, LOGGER)
            except Customer.DoesNotExist:
                customer = Customer(
                    prim_no=phone_number,
                    name=customer_name,
                    alt_no="",
                    cust_comm_mode="M",
                )
                customer.save()
                serializer = CustomerSerializer(customer)
                cus_id = serializer.data["id"]
                data = {"booked": False, "customer_id": cus_id,"booking_count":0,"booking_info":[]}
                response = response_builder(f"New customer created id: {str(cus_id)}",
                                            data,"success",201)
                return send_response(response, LOGGER)
        except Exception as e:
            response = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response, LOGGER)

class CustomerAuth(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        count = 3
        try:
            phone_number = request.data.get("phone_number")
            pin_number = request.data.get("pin_number")
            book_id = int(request.data.get("book_id"))
            if len(str(phone_number)) > 0 and len(str(phone_number)) > 10:
                phone_number = int(str(phone_number)[-10:])
            try:
                book = Book.objects.get(pk=book_id)
                customer = Customer.objects.get(
                    prim_no=phone_number,
                )
                if book.security_block == "Y":
                  response = response_builder("Your Locker has been Blocked due to 3 Failure Attempts...Please Contact admin",
                                            {},'failed',403)
                  return send_response(response, LOGGER)
                sec_ins = SecurityPin.objects.get(pk=book.sec_pin_id)
                sec_serializer = SecurityPinSerializer(sec_ins)
                password = sec_serializer.data["sec_pin_pin"]
                if password != make_hash(str(pin_number)):
                    sec_ins.attempt = sec_ins.attempt + 1
                    sec_ins.save()
                    attempts_left = count - sec_ins.attempt
                    if sec_ins.attempt == 3:
                        book.security_block = "Y"
                        book.save()
                    response = response_builder(f"Please check your password, you have {attempts_left} attempts Left.",
                                                {},'failed',401)
                    return send_response(response, LOGGER)
                else:
                    sec_ins.attempt = 0
                    sec_ins.save()
                    response = response_builder("Verified Successfully",{},'success',200)
                    return send_response(response, LOGGER)
            except (SecurityPin.DoesNotExist, Customer.DoesNotExist, Book.DoesNotExist) as err:
              if 'Book' in str(err):
                  model = "booking id"
              else:
                  model = "Customer"
              response = response_builder(f"{model} does not exist",str(err),'failed',400)
              return send_response(response, LOGGER)
        except Exception as e:
            response = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response, LOGGER)