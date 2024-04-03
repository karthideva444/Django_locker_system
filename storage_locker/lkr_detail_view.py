from .models import LkrSummary, BizLkrType, Book,Customer
from .serializers import  BizLkrTypeSerializer
from django.db.models import F, Sum, IntegerField, Case, When, Value
from rest_framework.views import APIView
from logging import LoggerAdapter
from users.utils import get_logger
from os.path import abspath, dirname
import os, requests, jwt
from .locker_utils import (BookInfoPayload, 
                           generate_numbers,
                           send_response,response_builder,
                           get_payment_link_or_estimate)
from rest_framework import generics
from utils import get_env
from rest_framework.decorators import api_view

internal_endpoint = get_env("INTERNAL_API_ENDPOINT")
secret_key = get_env("JWT_SECRET_KEY")

LOG_DIR = str(abspath(dirname(dirname(__file__)))) + os.sep
LOGGER_NAME = "Locker"
LOG_EXTRAS = {"process_name": "Locker Process"}
LOGGER = LoggerAdapter(
    get_logger(logger_name=LOGGER_NAME, log_file_path=LOG_DIR), extra=LOG_EXTRAS
)


class AvailLkrSummaryView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            biz_id, loc_id = str(kwargs["pk"]).split("-")
            if biz_id is not None and loc_id is not None:
                try:
                    LOGGER.info(
                        "Getting the Lockers for the business ID {} and location_id: {}".format(str(biz_id), str(loc_id))
                    )
                    lkr_summary = LkrSummary.objects.filter(biz=biz_id, location_id=loc_id)
                    if lkr_summary:
                        lkr_queryset = lkr_summary.filter(
                            status_cd__in=["A", "T"]
                        )
                        lkr_types = list(
                            lkr_queryset.values("lkr_type_id").annotate(
                                avail_lockers=Sum(
                                    Case(
                                        When(status_cd="A", then=F("status_count")),
                                        When(status_cd="T", then=-F("status_count")),
                                        default=Value(0),
                                        output_field=IntegerField(),
                                    )
                                )
                            )
                        )
                        lkr_available_ids = [
                            item["lkr_type_id"]
                            for item in lkr_types
                            if item["avail_lockers"] != 0
                        ]
                        if lkr_available_ids:
                            biz_lkr_queryset = BizLkrType.objects.filter(
                                id__in=lkr_available_ids
                            )
                            data = []
                            response_data = {}
                            for ind, biz_lkr in enumerate(biz_lkr_queryset):
                                biz_serializer = BizLkrTypeSerializer(biz_lkr)
                                biz_serializer_data = biz_serializer.data
                                biz_serializer_data["lkr_type_id"] = str(biz_lkr.id)
                                biz_serializer_data['amt_initial'] = int(float(biz_serializer_data[
                                    'amt_initial']) + float(biz_serializer_data['processing_fee']))
                                biz_serializer_data['amt_per_unit'] = int(float(biz_serializer_data['amt_per_unit']))
                                biz_serializer_data['incremental_units'] = generate_numbers(
                                    biz_serializer_data['min_hr'],
                                    biz_serializer_data['max_hr'],
                                    biz_serializer_data['increment_units']
                                    )
                                del biz_serializer_data['processing_fee']
                                del biz_serializer_data['increment_units']
                                del biz_serializer_data['max_hr']
                                biz_serializer_data[
                                    "image_url"
                                ] = request.build_absolute_uri(
                                    biz_serializer_data["image_url"]
                                )
                                biz_serializer_data['biz'] = '{}-{}'.format(biz_id, loc_id)
                                data.append(biz_serializer_data)
                            response_data['available_type_count'] =  len(data)
                            response_data['available_type_all'] = data
                            response = response_builder("Lockers Available for this business ID and location_id",
                                    response_data,'success',200)
                            return send_response(response, LOGGER)
                        response = response_builder("Sorry ,All the Lockers are Booked for this business ID and location_id",
                                {"biz":biz_id,"loc_id":loc_id},'failed',306)
                        return send_response(response, LOGGER)
                    response = response_builder("Sorry ,no lockers are available for this business ID and location_id",
                                {"biz":biz_id,"loc_id":loc_id},'failed',404)
                    return send_response(response, LOGGER)
                except LkrSummary.DoesNotExist:
                    response = response_builder("please check the biz_id and loc_id",
                                {"biz":biz_id,"loc_id":loc_id},'failed',400)
                    return send_response(response, LOGGER)
            else:
                response = response_builder("biz_id and loc_id are missing",{},'failed',400)
                return send_response(response, LOGGER)
        except Exception as e:
            response = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response, LOGGER)


class BookInfoView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            book_id = kwargs["pk"]
            bookdata = Book.objects.get(pk=book_id)
            cus_ins = Customer.objects.get(pk=bookdata.cust_id)
            payload = BookInfoPayload(bookdata, cus_ins)
            response = response_builder("Booking info Retreived",payload,'success',200)
            return send_response(response, LOGGER)
        except Book.DoesNotExist as e:
            response = response_builder("Book id does not exist",{"book_id":book_id},'failed',400)
            return send_response(response, LOGGER)
        except Exception as e:
            response = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response, LOGGER)
        
class GetAmount(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            required_fields = ['booking_hrs', 'biz', 'lkr_type_id', 'booking_id', 'payment_link']
            for field in required_fields:
                if field not in data:
                    LOGGER.error(f"Missing required field: {field}")
                    raise ValueError(f"Missing required field: {field}")
            for field, value in data.items():
                if field not in ['payment_link', 'biz', 'booking_id'] and (
                    not isinstance(value, str)  or
                         not value.isdigit() or int(value) < 0):
                    LOGGER.error(f"Invalid value for {field}: {value}")
                    raise ValueError(f"Invalid value for {field}: {value}")
            if 'payment_link' in data and eval(data['payment_link']) not in [True, False]:
                LOGGER.error("Invalid value for payment_link, should be True or False")
                raise ValueError("Invalid value for payment_link, should be True or False")

            booking_hrs = int(data['booking_hrs'])
            biz_id, loc_id = str(data['biz']).split('-')
            lkr_type_id = str(data['lkr_type_id'])
            try:
                booking_id = int(data['booking_id']) if 'booking_id' in data and data['booking_id'].isdigit() else None
            except (KeyError, ValueError, AttributeError):
                booking_id = None
            payment_link = eval(data['payment_link'])
            response_data = get_payment_link_or_estimate(request,payment_link,booking_id,booking_hrs,
                                                         biz_id,lkr_type_id,loc_id,'Extend','Book')
            return send_response(response_data, LOGGER)
        except ValueError as ve:
            response = response_builder("value error",str(ve),'failed',400)
            return send_response(response, LOGGER)
        except Exception as e:
            response = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response, LOGGER)
        

@api_view(http_method_names=["GET"])
def bookingpage(request, *args, **kwargs):
  try:
    payload = jwt.decode(kwargs['token'],secret_key, algorithms=['HS256'])
    url = internal_endpoint + '/api/availLkrDetail/' + payload['biz_id'] +'/'
    token = request.headers.get('Authorization')
    headers = {"Content-type": "application/json", 'Authorization': token}
    response = requests.get(url, headers=headers).json()
    response['data']['phone_number'] = payload['mn']
    return send_response(response, LOGGER)
  except Exception as exp:
    response = response_builder("Bad Request",str(exp),'failed',400)
    return send_response(response, LOGGER)     
