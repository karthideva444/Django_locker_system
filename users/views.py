from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import UserSerializer
from rest_framework import status
from logging import LoggerAdapter
from .utils import get_logger
from storage_locker.models import Employee,BizLocation,Customer, Book
from django.contrib.auth import login, logout
from os.path import abspath, dirname
import os
from django.urls import reverse
from storage_locker.locker_utils import Invoice_Gen,open_locker_response, to_datetime, response_builder,send_response, calling_webhook
from datetime import datetime
from datetime import timedelta
import json
from decimal import Decimal
LOG_DIR = str(abspath(dirname(dirname(__file__)))) + os.sep
LOGGER_NAME = "Authentication"
LOG_EXTRAS = {"process_name": "UserAuth Process"}
LOGGER = LoggerAdapter(
    get_logger(logger_name=LOGGER_NAME, log_file_path=LOG_DIR), extra=LOG_EXTRAS
)

def decimal_default(obj):
    if isinstance(obj, (Decimal, datetime.timedelta)):
        return float(obj)
    raise TypeError


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            userdata = request.data
            if "username" not in userdata or "password" not in userdata:
                return Response(
                    {"error": "Both username and password are Required."},
                    status=HTTP_400_BAD_REQUEST,
                )
            user = authenticate(
                request, username=userdata["username"], password=userdata["password"]
            )
            if user is not None:
                login(request, user)
                serializer = UserSerializer(user)
                user_id = serializer.data["id"]
                emp = Employee.objects.get(user_id=user_id)
                loc = BizLocation.objects.get(biz_id=emp.biz)
                b_loc_id = "{}-{}".format(loc.biz_id, loc.location_id)
                response_data = {"biz": b_loc_id, "session_id": request.session.session_key, "code":200}
                LOGGER.info(
                    "{} has been logged in successfully".format(
                        serializer.data["username"]
                    )
                )
                return Response(response_data, status=HTTP_200_OK)
            else:
                # User credentials are not valid
                LOGGER.error("Invalid credentials")
                return Response(
                    {"error": "Invalid credentials","code":400}, status=HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            response_data = {"msg": "Internal Server Error", "code": 500}
            LOGGER.error("Exception Occured: {}".format(str(e)))
            return Response(response_data,status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    if request.method == "POST":
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            username = serializer.validated_data.get("username")
            email = serializer.validated_data.get("email")

            if User.objects.filter(username=username).exists():
                return Response(
                    {"error": "Username is already in use.", "code":400},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if User.objects.filter(email=email).exists():
                return Response(
                    {"error": "Email address is already in use.","code":400},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # If all custom validations pass, save the user
            serializer.save()
            response_data = {
                "message": "Registration successful",
                "username": serializer.data["username"],
                "email": serializer.data["email"],
                "code":201
            }
            LOGGER.info(
                "{} has been registered successfully".format(
                    serializer.data["username"]
                )
            )
            return Response(response_data, status=status.HTTP_201_CREATED)
        LOGGER.error("Registration failed with error: {}".format(serializer.errors))
        response_data = {"msg":serializer.errors, "code":400}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)



class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # Logout the user
            logout(request)
            LOGGER.info("User has been logged out successfully")
            return Response({"msg": "Logout successful", "code": 200},
                             status=status.HTTP_200_OK)
        except Exception as e:
            response_data = {"msg": "Internal Server Error", "code": 500}
            LOGGER.error("Exception Occured: {}".format(str(e)))
            return Response(response_data,status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            old_book = Book.objects.get(pk=102)
            booked_time = old_book.start_dt + timedelta(hours=5, minutes=30)
            booked_duration = old_book.booked_duration
            booking_hr = datetime.strptime(str(booked_duration), "%H:%M:%S").time().hour
            est_endtime = {"start_time":to_datetime(booked_time)
                        ,"booked_duration":booking_hr}
            customer = Customer.objects.get(pk=1)
            invoice = Invoice_Gen(customer, old_book, 1015, 'chennai')
            data = open_locker_response(1015,invoice,invoice['amount_paid'],{},est_endtime)
            response_data = response_builder("Locker Open and release",data,'success',202)
            print(response_data)
            try:
                calling_webhook(response_data, 1, 'release')
            except Exception as expected:
                print(expected)
                return Response({"err":expected})
            print(response_data)
            # data = request.data
            # detail_url = request.build_absolute_uri(reverse('RazorPayViewURL'))
        except Exception as err:
            return Response({"err":err})
        return send_response(response_data,LOGGER)
