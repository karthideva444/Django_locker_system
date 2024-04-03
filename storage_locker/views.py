from rest_framework import generics
from decimal import Decimal
from logging import LoggerAdapter
from datetime import datetime, timedelta
from datetime import time as tt
from django.db.models import F, Case, When,IntegerField
from users.utils import get_logger
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from permissions.permissions import IsRazorpay
from .serializers import (
    PrebookSerializer,
    SecurityPinSerializer,
)
from payments.payment_utils import call_internal_api
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .locker_utils import (
    check_lkr_availability,
    get_prebook_data,
    make_hash,
    locker_function,
    CheckAvailLocker,
    calculate_total_time,
    create_dict,
    Invoice_Gen,
    locker_release,
    calculate_amount_in_units,
    update_activity,
    booking,
    SaveSecurityInstance,
    send_response,
    response_builder,
    to_datetime,
    open_locker_response,
    get_payment_link_or_estimate,
    get_booking_info, 
    get_booking_fields,
    GetUserType,
    calling_webhook,
    AddPaymentEntry,
    confirm_api_response,
    is_valid_booking_token,
    update_book_token
)
from .response import (
    PaymentGatewayResponse,
    zero_payment_response,
    build_callback_response)
from .models import (
    LkrSummary,
    Customer,
    Book,
    Prebook,
    SecurityPin,
    BizLkr,
    BusinessInfo,
    BizLkrType,
    LkrStatusLog,
    BizLocation,
    Employee,
    Payment,
    BookToken
)
from os.path import abspath, dirname
import os, time

LOG_DIR = str(abspath(dirname(dirname(__file__)))) + os.sep
LOGGER_NAME = "Locker"
LOG_EXTRAS = {"process_name": "Locker Process"}
LOGGER = LoggerAdapter(
    get_logger(logger_name=LOGGER_NAME, log_file_path=LOG_DIR), extra=LOG_EXTRAS
)
from utils.get_env_utils import get_env
payment_method = get_env("PAYMENT_METHOD")




class BusinessLocationView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        try:
            user_id = request.user.id
            emp = Employee.objects.get(user_id=user_id)
            bloc_id = '{}-{}'.format(emp.biz, emp.location_id)
            response = response_builder("Business for the user",{"biz":bloc_id},"success",200)
            return send_response(response, LOGGER)
        except Employee.DoesNotExist:
            response = response_builder("Employee not found for the given user_id.",{},"error",404)
            return send_response(response, LOGGER)
        except Exception as e:
            response = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response, LOGGER)

class AvailLockerView(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        biz_id, loc_id = str(kwargs["pk"]).split("-")
        bloc = BizLocation.objects.get(biz_id=biz_id, location_id=loc_id)
        response = CheckAvailLocker(
            kwargs, biz_id, bloc.loc_name, loc_id, check_lkr_availability, LkrSummary
        )
        return send_response(response, LOGGER)


class PreBookView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        try:
            # Input validation
            required_fields = ["biz", "locker_type_id", "phone_number", "pin", "booking_hrs"]
            for field in required_fields:
                if field not in request.data:
                    response = response_builder(f"Missing required field: {field}",{},'failed',400)
                    return send_response(response, LOGGER)
            booking_token = request.headers.get("Booking-Token",None)
            phone_number = int(request.data["phone_number"])
            biz_id, loc_id = str(request.data["biz"]).split("-")
            if booking_token is not None:
                # if not booking_token:
                #     # If booking token is missing, return a response indicating the issue
                #     response = response_builder("Booking token is missing in the headers", {}, 'failed', 400)
                #     return send_response(response, LOGGER)
                token_data = is_valid_booking_token(booking_token)
                if not token_data:
                    # If the booking token is not valid, return an appropriate response
                    response = response_builder("Session Expired", {}, 'failed', 400)
                    return send_response(response, LOGGER)
                else:
                    phone_number = token_data['mn']
                    biz_id, loc_id = str(token_data["biz"]).split("-")
                try:
                    token = BookToken.objects.get(token=booking_token)
                    if token.pbook is not None:
                        response = response_builder("Session Expired", {}, 'failed', 400)
                        return send_response(response, LOGGER)
                except:
                    pass

            # Additional validation
            booking_hrs = int(request.data["booking_hrs"])
            booked_duration = str(tt(booking_hrs, 0))
            locker_type_id = int(request.data["locker_type_id"])
            pin = int(request.data["pin"])

            if len(str(phone_number)) > 0 and len(str(phone_number)) > 10:
                phone_number = int(str(phone_number)[-10:])

            if ( not str(pin).isdigit() or len(str(pin)) != 4 ):
                response = response_builder("Invalid PIN. It must be a 4-digit number.",{},'failed',400)
                return send_response(response, LOGGER)

            if not str(phone_number).isdigit() or len(str(phone_number)) != 10:
                response = response_builder("Invalid phone number. It must be a 10-digit number.",{},'failed',400)
                return send_response(response, LOGGER)
            
            if not str(booking_hrs).isdigit() or booking_hrs  > 24 or booking_hrs < 1:
                response = response_builder("Booking hour must be between 1 to 24",{},'failed',400)
                return send_response(response, LOGGER)

            total_avail = check_lkr_availability(LkrSummary, biz_id, loc_id)
            if total_avail <= 0:
                response = response_builder("No available lockers for booking.",{},'failed',404)
                return send_response(response, LOGGER)

            customer_instance = Customer.objects.get(prim_no=phone_number)
            biz_location = BizLocation.objects.get(biz_id=biz_id, location_id=loc_id)
            biz_instance = BusinessInfo.objects.get(pk=biz_location.biz_info_id)
            lkr_type_instance = BizLkrType.objects.get(pk=locker_type_id, location_id=loc_id, biz_id=biz_id)
            data = calculate_amount_in_units(booking_hrs, biz_id, locker_type_id,loc_id,False)
            amount = int(data['amount'])
            amount_p = amount * 100
            prebook_instance = Prebook(
                cust=customer_instance,
                biz=biz_instance,
                lkr_type=lkr_type_instance,
                amount_init=amount,
                booking_hrs=booked_duration,
                location_id = loc_id,
                emp_id = request.user.id
            )
            prebook_instance.save()
            update_activity(None, "prebook", request.user.id, biz_id, loc_id, customer_instance.id)
            lkrsummary = LkrSummary.objects.filter(
                biz__id=biz_id, lkr_type__id=locker_type_id,location_id = loc_id
            )
            lkrsummary.update(
                status_count=Case(
                    When(status_cd="T", then=F("status_count") + 1),
                    When(status_cd="A", then=F("status_count") - 1),
                    default=F("status_count"),  # Keep count unchanged for other status codes
                    output_field=IntegerField(),
                ),
                updated_dt=timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            prebook_id = prebook_instance.id
            reference_id = (
                "P" + str(prebook_id) + datetime.now().strftime("%Y%m%d%H%M%S")  + str(request.user.id)
            )
            data = create_dict(
                amount=amount_p, contact=phone_number, reference_id=reference_id, 
                booked_duration=booked_duration 
            )
            if int(amount_p) != 0:
                request_payload, response = call_internal_api(request, data, 'Book','Prebook')
                LOGGER.info("request_payload: {}".format(request_payload))
                LOGGER.info("response_payload: {}".format(response))
                try:
                    if response['success']:
                        response = PaymentGatewayResponse(response, amount)
                        response['booked'] = False
                        response['locker_type_id'] = locker_type_id
                        response['contact'] = phone_number
                        response_data = response_builder("Prebook Successful",response,"success",201)
                        SaveSecurityInstance(prebook_instance, phone_number, pin)
                        AddPaymentEntry(biz_id,loc_id,None,reference_id,'prebook',amount,'Book', 
                        request_payload,booked_duration,customer_instance.id)
                    else:
                        response = response_builder("Payment Failed",response,'failed',400)
                        return send_response(response, LOGGER)
                except Exception as e:
                    response_data = response_builder("Bad Request", {"error":str(e)},"failed",400)
                prebook_instance.pay_req_json = request_payload
                prebook_instance.pay_res_json = response
                prebook_instance.reference_id = reference_id
                prebook_instance.save()
                update_book_token(booking_token,prebook_id)
                return send_response(response_data, LOGGER)
            else:
                prebook_instance.reference_id = reference_id
                prebook_instance.save()
                response = zero_payment_response(data)
                response['locker_type_id'] = locker_type_id
                response['amount'] = amount
                response_data = response_builder("Prebook Successfull",response,"success",201)
                SaveSecurityInstance(prebook_instance, phone_number, pin)
                update_book_token(booking_token,prebook_id)
                return send_response(response_data, LOGGER)
        except ValueError as error:
            response = response_builder("ValueError",str(error),'failed',400)
            return send_response(response, LOGGER)
        except (Customer.DoesNotExist,BizLkrType.DoesNotExist, BusinessInfo.DoesNotExist) as err:
            if 'Book' in str(err):
                msg = "booking id does not exist"
            elif 'Customer' in str(err):
                msg = 'phone number does not exist'
            elif 'BusinessInfo' in str(err):
                msg = 'Invalid business and location'
            elif 'BizLkrType' in str(err):
                msg = 'Locker type number does not exist'
            else:
                msg = '''There are no lockers available
                for this business {} and location {}'''.format(biz_id, loc_id)
            response = response_builder("Bad request",msg,'failed',400)
            return send_response(response, LOGGER)
        except Exception as e:
            response = response_builder("Internal Server Error",e,'failed',500)
            return send_response(response, LOGGER)


class ConfirmationView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            prebook = Prebook.objects.get(reference_id=kwargs["pk"])
            prebookid = prebook.id
            book_hrs = prebook.booking_hrs.seconds // 3600
            loc = prebook.location_id
            cust_id = prebook.cust_id
            emp_id = request.user.id
            serializer = PrebookSerializer(prebook).data
            if prebook.amount_init ==0:
                try:
                    book = Book.objects.get(pbook_id = prebookid)
                    response = confirm_api_response(prebookid, serializer)
                    return send_response(response,LOGGER)
                except:
                    pass
                prebook.payment_status = "P"
                prebook.save()
                b_duration = str(tt(book_hrs, 0))
                sec_pin_id,cus_ins,biz_ins,bizlkr_ins = get_booking_fields(prebook)
                if bizlkr_ins is None:
                    response = response_builder("Currently there are no lockers available",
                                                {},'failed',204)
                    return send_response(response,LOGGER)
                #  Locker open condition needs to be implemented
                new_book, new_book_id = booking(cus_ins,biz_ins,bizlkr_ins,prebookid,sec_pin_id,
                        prebook.amount_init,None,None,b_duration,loc, emp_id)
                book_ref_id = (
                "B" + str(new_book_id) + datetime.now().strftime("%Y%m%d%H%M%S") + str(emp_id)
                    )
                new_book.book_ref_id = book_ref_id
                new_book.save()
                response = confirm_api_response(prebookid, serializer)
                user = GetUserType(request)
                if user == 'WhatsApp':
                    calling_webhook(response, cust_id, 'book')
                return send_response(response, LOGGER)
            cur_timestamp = datetime.now().time()
            cur_time_nxt_min = (
                datetime.combine(datetime.today(), cur_timestamp) + timedelta(minutes=1)
            ).time()
            while True:
                payment_status = serializer["payment_status"]
                if datetime.now().time() > cur_time_nxt_min:
                    response = response_builder("PAYMENT_REQUIRED",{},'failed',402)
                    return send_response(response, LOGGER)
                if payment_status == "P":
                    response = confirm_api_response(prebookid, serializer)
                    calling_webhook(response, cust_id, 'book')
                    return send_response(response, LOGGER)
                time.sleep(1)
        except Prebook.DoesNotExist as e:
            response = response_builder("prebook id not exist",{},'failed',400)
            return send_response(response, LOGGER)          
        except Exception as e:
            response = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response, LOGGER)


class AvailLkrLoc(APIView):
    def get(self, request, *args, **kwargs):
        try:
            Location, biz_id, loc_id = BizLocation.objects.filter(location_id=kwargs["pk"]).values_list(
                "loc_name", "biz_id","location_id"
            ).first() or (None, None, None)
            if Location is None and biz_id is None and loc_id is None:
                response = response_builder("No Business Available",{"location_id":kwargs["pk"]},'failed',400)
                return send_response(response, LOGGER)
 
            response = CheckAvailLocker(
                kwargs, biz_id, Location, loc_id, check_lkr_availability, LkrSummary
            )
            return send_response(response, LOGGER)
        except Exception as e:
            response_data = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response_data, LOGGER)
        
class AvailLkrLocToken(APIView):
    def get(self, request, *args, **kwargs):
        biz_id, loc_id = str(kwargs["pk"]).split("-")
        phone_number = kwargs['mn']
        if len(str(phone_number)) > 0 and len(str(phone_number)) > 10:
            phone_number = int(str(phone_number)[-10:])

        if not str(phone_number).isdigit() or len(str(phone_number)) != 10:
            response = response_builder("Invalid phone number. It must be a 10-digit number.",{},'failed',400)
            return send_response(response, LOGGER)
        bloc = BizLocation.objects.get(biz_id=biz_id, location_id=loc_id)
        response = CheckAvailLocker(
            kwargs, biz_id, bloc.loc_name, loc_id, check_lkr_availability, LkrSummary
        )
        if response['code'] == 200:
            booktoken = BookToken(token=response['data']['token'])
            booktoken.save()
            del response['data']['token']
        return send_response(response, LOGGER)

class OpenLockerView(APIView):
    def post(self, request, *args, **kwargs):
        count = 3
        try:
            data = request.data
            required_fields = ["booking_id", "phone_number", "sec_pin","release","role"]
            for field in required_fields:
                if field not in request.data:
                    response = response_builder(f"Missing required field: {field}",{},'failed',400)
                    return send_response(response, LOGGER)
            phone_number = int(request.data["phone_number"])
            booking_id = int(request.data["booking_id"])
            release = request.data.get("release","")
            if len(str(booking_id)) <=0 or not str(booking_id).isdigit():
                response = response_builder("Please enter the valid booking_id",
                                        {"booking_id":booking_id},'failed',400)
                return send_response(response, LOGGER)
 
            if release  not in ['Y','N']:
                response = response_builder("Release value must be Y or N",{},'failed',400)
                return send_response(response, LOGGER)
            
            if len(str(phone_number)) > 0 and len(str(phone_number)) > 10:
                phone_number = int(str(phone_number)[-10:])

            if not str(phone_number).isdigit() or len(str(phone_number)) != 10:
                response = response_builder("Invalid phone number. It must be a 10-digit number.",
                                            {"phone_number":phone_number},'failed',400)
                return send_response(response, LOGGER)
   
            book = Book.objects.get(pk=booking_id)
            if not book.active_boo:
                response_data = response_builder("There is no booking available",{},'failed',400)
                return send_response(response_data, LOGGER)
            customer = Customer.objects.get(prim_no=phone_number)
            cust_id = customer.id
            prebook = Prebook.objects.get(pk = book.pbook_id)
            bizlkr_id = book.biz_lkr_id
            biz_lkr = BizLkr.objects.get(pk=bizlkr_id)
            lkr_type_id = biz_lkr.lkr_type_id
            if book.security_block == "Y":
                response = response_builder(
                "Your Locker has been Blocked due to 3 Failure Attempts...Please Contact admin",
                {},'failed',403)
                return send_response(response, LOGGER)

            if data["role"] != "WhatsApp":
                sec_ins = SecurityPin.objects.get(pk=book.sec_pin_id)
                sec_serializer = SecurityPinSerializer(sec_ins)
                password = sec_serializer.data["sec_pin_pin"]
                if password != make_hash(str(data["sec_pin"])):
                    sec_ins.attempt = sec_ins.attempt + 1
                    sec_ins.save()
                    attempts_left = count - sec_ins.attempt
                    if sec_ins.attempt == 3:
                        book.security_block = "Y"
                        book.save()
                    response = response_builder(
                    f"Please check your password, you have {attempts_left} attempts Left.",
                    {},'failed',401)
                    return send_response(response, LOGGER)
                else:
                    sec_ins.attempt = 0
                    sec_ins.save()
            if book:
                booked_time = book.start_dt + timedelta(hours=5, minutes=30)
                loc_id = book.location_id
                bloc = BizLocation.objects.get(location_id=loc_id)
                loc_name = bloc.loc_name
                biz_id = book.biz_id
                booked_duration = book.booked_duration
                booking_hr = datetime.strptime(str(booked_duration), "%H:%M:%S").time().hour
                days, hours, minutes= calculate_total_time(booked_time)
                cur_time = timedelta(days=days,hours=hours,minutes=minutes)
                invoice = Invoice_Gen(customer, book, biz_lkr.lock_no, loc_name)
                est_endtime = {"start_time":to_datetime(booked_time)
                               ,"booked_duration":booking_hr}
                # The below condition is for 
                # when current time lesser then booking hours and the locker is paid or free
                #  and the customer doesn't want to release the locker and want to only open the locker
                if (timedelta(hours=booking_hr) > cur_time  and release == 'N') or (
                    timedelta(hours=booking_hr) > cur_time  and release == 'N' and invoice[
                    'balance_amount'] == 0 and invoice['amount_paid'] == 0):
                    data = open_locker_response(biz_lkr.lock_no,{},0,{},est_endtime)
                    update_activity(book.id, "Open", request.user.id, biz_id, loc_id, cust_id)
                    response_data = response_builder("Locker Opened",data,'success',200)
                    return send_response(response_data, LOGGER) 
                
                # # This condition is  used for 
                # # when current time lesser then booking hours and the locker is paid or free
                # #  and the customer  want to release the locker.
                elif (timedelta(hours=booking_hr) > cur_time and release == 'Y')or (
                    timedelta(hours=booking_hr) > cur_time  and release == 'Y' and invoice[
                    'balance_amount'] == 0 and invoice['amount_paid'] == 0):
                    locker_release(biz_lkr.lock_no, biz_id,book.id,loc_id, LOGGER)
                    data = open_locker_response(biz_lkr.lock_no,invoice,invoice['balance_amount'],{},est_endtime)
                    update_activity(book.id, "Open & Release", request.user.id, biz_id, loc_id, cust_id) 
                    response_data = response_builder("Locker Open and release",invoice,'success',202)
                    return send_response(response_data, LOGGER) 
                # # The below condition is for 
                # # when current time greater then booking hours and the locker is free, hence the amount is zero
                # #  and the customer doesn't want to release the locker and want to only open the locker
                elif timedelta(hours=booking_hr) < cur_time and release == 'N' and invoice[
                    'balance_amount'] == 0 and invoice['amount_paid'] == 0:
                    
                    data = open_locker_response(biz_lkr.lock_no,{},0,{},est_endtime)
                    update_activity(book.id, "Open", request.user.id, biz_id, loc_id, cust_id)
                    response_data = response_builder("Locker Opened",data,'success',200)
                    return send_response(response_data, LOGGER)  
                # # This condition is  used for 
                # # when current time greater then booking hours and the locker is free, hence the amount is zero
                # #  and the customer  want to release the locker.
                elif timedelta(hours=booking_hr) < cur_time and release == 'Y' and invoice[
                    'balance_amount'] == 0 and invoice['amount_paid'] == 0:
                    
                    locker_release(biz_lkr.lock_no, biz_id,book.id,loc_id, LOGGER)
                    data = open_locker_response(biz_lkr.lock_no,invoice,0,{},est_endtime)
                    update_activity(book.id, "Open & Release", request.user.id, biz_id, loc_id, cust_id)
                    response_data = response_builder("Locker Open and release",data,'success',202)
                    return send_response(response_data, LOGGER)
                else:
                    estimation = get_payment_link_or_estimate(
                    request,True,book.id,booking_hr,biz_id,lkr_type_id,loc_id,'Release',"Book", days, hours)
                    booking_info = get_booking_info(estimation,invoice, prebook)
                    data = open_locker_response(biz_lkr.lock_no, invoice, invoice['balance_amount'], booking_info,est_endtime)
                    # update_activity(book.id, "Pay & Release", request.user.id, biz_id, loc_id, cust_id)
                    response_data = response_builder("Pay and Release",data,'success',201)
                    return send_response(response_data, LOGGER)
            else:
                response_data = response_builder("There is no booking available",{},'failed',400)
                return send_response(response_data, LOGGER)
        except (SecurityPin.DoesNotExist, Customer.DoesNotExist, Book.DoesNotExist) as e:
            response_data = response_builder("There is no booking available",str(e),'failed',400)
            return send_response(response_data, LOGGER)
        except Exception as e:
            response_data = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response_data, LOGGER)

@method_decorator(csrf_exempt, name='dispatch')
class CallbackView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        try:
            response = request.data
            LOGGER.info("callback_data {}".format(response))
            LOGGER.info("request.headers {}".format(request.headers))
            ref_id, initiated_by, resp = build_callback_response(response)
            if ref_id is not None:
                payment = Payment.objects.get(ref_id=ref_id)
                if payment.payment_status != 'O': #O, P F
                    response_data = response_builder("Duplicate Callback",{},'failed',400)
                    return send_response(response_data, LOGGER) 
                if 'P' in ref_id:
                    prebook = Prebook.objects.get(reference_id=ref_id)
                    serializer = PrebookSerializer(prebook).data
                    pid = prebook.id
                    amount = serializer['amount_init']
                    booked_duration = serializer['booking_hrs']
                    prebook.payment_status = "P"
                    prebook.save()
                    sec_pin_id = SecurityPin.objects.values_list("pk", flat=True).get(
                        sec_pin_pbook_id=pid
                    )
                    loc_id = prebook.location_id
                    cust_id, biz_id, lkr_type_id, pay_req = get_prebook_data(prebook)
                    customer_instance = Customer.objects.get(pk=cust_id)
                    biz_instance = BusinessInfo.objects.get(pk=biz_id)
                    biz_lkr_instance = locker_function(
                        BizLkr, LkrSummary, LkrStatusLog, biz_id, lkr_type_id, loc_id
                    )
                    new_book,book_id =  booking(customer_instance,biz_instance,biz_lkr_instance,
                            pid, sec_pin_id, amount, pay_req, 
                            resp, booked_duration,loc_id, initiated_by)
                    payment.book_id = book_id
                    payment.payment_status = 'P'
                    payment.pay_res = resp
                    payment.save()
                    book_ref_id = (
                    "B" + str(book_id) + datetime.now().strftime("%Y%m%d%H%M%S") + str(initiated_by)
                        )
                    new_book.book_ref_id = book_ref_id
                    new_book.save()
                    response = confirm_api_response(pid, serializer)
                    emp = Employee.objects.get(user_id=initiated_by)
                    user = emp.usertype
                    # user = GetUserType(request)
                    LOGGER.info("GetUserType {}".format(user))
                    update_activity(new_book.id, "Book", initiated_by, biz_id, loc_id, cust_id)
                    if user == 'WhatsApp':
                        calling_webhook(response, cust_id, 'book')
                    return send_response(response,LOGGER)
                else:
                    old_book = Book.objects.get(book_ref_id=ref_id)
                    biz_id, loc_id = old_book.biz_id, old_book.location_id
                    old_book.advance_amt = old_book.advance_amt + Decimal(resp['data']['amount'] / 100)
                    booked_time = old_book.start_dt + timedelta(hours=5, minutes=30)
                    booked_duration = old_book.booked_duration
                    booking_hr = datetime.strptime(str(booked_duration), "%H:%M:%S").time().hour
                    est_endtime = {"start_time":to_datetime(booked_time)
                               ,"booked_duration":booking_hr}
                    old_book.save()
                    prebook = Prebook.objects.get(id=old_book.pbook_id)
                    customer = Customer.objects.get(pk=prebook.cust_id)
                    serializer = PrebookSerializer(prebook).data
                    payment.book_id = old_book.id
                    payment.payment_status = 'P'
                    payment.pay_res = resp
                    payment.save()
                    if payment.intent == 'Extend':
                        response = confirm_api_response(prebook.id, serializer)
                        old_book.booked_duration = old_book.booked_duration + payment.extended_duration
                        old_book.save()
                        emp = Employee.objects.get(user_id=initiated_by)
                        user = emp.usertype
                        LOGGER.info("Response Data {}". format(response))
                        LOGGER.info("GetUserType {}".format(user))
                        update_activity(old_book.id, "Extend", initiated_by, biz_id, loc_id, prebook.cust_id)
                        if user == 'WhatsApp':
                            calling_webhook(response, prebook.cust_id, 'extend')
                        return send_response(response,LOGGER)
                    else:
                        bizlkr_id = old_book.biz_lkr_id
                        bloc = BizLocation.objects.get(location_id=old_book.location_id)
                        loc_name = bloc.loc_name
                        biz_lkr = BizLkr.objects.get(pk=bizlkr_id)
                        invoice = Invoice_Gen(customer, old_book, biz_lkr.lock_no, loc_name)
                        old_book.duration = timedelta(
                            days=invoice['duration']['days'], 
                            hours=invoice['duration']['hours'], 
                            minutes=invoice['duration']['minutes']
                            )
                        old_book.tot_lock_fee = invoice['total_amount']
                        old_book.oth_chrgs = 0
                        old_book.save()
                        locker_release(biz_lkr.lock_no, old_book.biz_id,old_book.id,old_book.location_id, LOGGER)
                        update_activity(old_book.id, "Open & Release", initiated_by, biz_id, loc_id, prebook.cust_id)
                        data = open_locker_response(biz_lkr.lock_no,invoice,invoice['amount_paid'],{},est_endtime)
                        response_data = response_builder("Locker Open and release",data,'success',202)
                        LOGGER.info("Response Data {}". format(response_data))
                        emp = Employee.objects.get(user_id=initiated_by)
                        user = emp.usertype
                        LOGGER.info("GetUserType {}".format(user))
                        if user == 'WhatsApp':
                            calling_webhook(response_data, prebook.cust_id, 'release')
                        return send_response(response_data,LOGGER)
            response_data = response_builder("payment Failed",resp,'failed',400)
            return send_response(response_data, LOGGER) 
        except (Payment.DoesNotExist, Customer.DoesNotExist, BusinessInfo.DoesNotExist, Prebook.DoesNotExist,
                BizLkr.DoesNotExist, BizLocation.DoesNotExist, Book.DoesNotExist, SecurityPin.DoesNotExist,
                Employee.DoesNotExist) as err:
            response_data = response_builder("Does not Exist",str(err),'failed',400)
            return send_response(response_data, LOGGER)      
        except Exception as e:
            response_data = response_builder("Internal Server Error",str(e),'failed',500)
            return send_response(response_data, LOGGER)

        #     success = callback_data.get("success")
        #     code = callback_data.get("code")
        #     transaction_id = callback_data.get("data", {}).get("transactionId","")
        #     prebook_id = transaction_id[1:-14]
        #     booked_duration =  callback_data.get("data", {}).get("booked_duration","")
        #     try:
        #         book = Book.objects.get(pbook_id=prebook_id)
        #         response_data = {
        #             "status": "failed",
        #             "message": "Locker already booked for this Prebook ID",
        #             "code": 400,
        #         }
        #         LOGGER.warn("Locker already booked for this Prebook ID: {}".format(prebook_id))
        #         return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        #     except:
        #         pass
        #     prebook = Prebook.objects.get(pk=prebook_id)
        #     loc_id = prebook.location_id
        #     if success and code == "PAYMENT_SUCCESS":
        #         # Payment successful
        #         amount = callback_data.get("data", {}).get("amount")
        #         response_data = {
        #             "status": "success",
        #             "message": "Payment successful",
        #             "transaction_id": transaction_id,
        #             "amount": amount,
        #         }
        #         try:
        #             prebook.payment_status = "P"
        #             prebook.save()
        #             sec_pin_id = SecurityPin.objects.values_list("pk", flat=True).get(
        #                 sec_pin_pbook_id=prebook_id
        #             )
        #             cust_id, biz_id, lkr_type_id, pay_req = get_prebook_data(prebook)
        #             customer_instance = Customer.objects.get(pk=cust_id)
        #             biz_instance = BusinessInfo.objects.get(pk=biz_id)
        #             biz_lkr_instance = locker_function(
        #                 BizLkr, LkrSummary, LkrStatusLog, biz_id, lkr_type_id, loc_id
        #             )
        #             if biz_lkr_instance is None:
        #                 response_data = {"status": "failed",
        #                 "message": "Currently there are no lockers  available", "code":204}
        #                 LOGGER.warn("Currently there are no lockers  available")
        #                 return Response(response_data, status.HTTP_204_NO_CONTENT)
        #             book_id =  booking(customer_instance,biz_instance,biz_lkr_instance,
        #                         prebook_id, sec_pin_id, amount, pay_req, 
        #                         callback_data, booked_duration,loc_id)
        #             response_data['code'] = 200
        #             response_data['book_id'] = book_id
        #             LOGGER.info("Booking successful for booking id: {}".format(book_id))
        #             return Response(response_data, status.HTTP_200_OK)
        #             # payload, biz_instance = build_mqtt_payload(biz_id,biz_lkr_instance.lock_no)
        #             # response = PublishSend(payload, biz_instance, LOGGER)
        #             # update_activity(book_id, "Booked", request.user.id)
        #             # if response['message'] != 'success':
        #             #     response_data = {"status": "error", "message": 'Error From Message queue','code':500}
        #             #     return Response(response_data, status.HTTP_500_INTERNAL_SERVER_ERROR)
        #         except Exception as e:
        #             prebook.payment_status = "F"
        #             prebook.save()
        #             LOGGER.error(f"Exception Occurred: {str(e)}")
        #             return Response(
        #                 {"status": "failed","message": "Invalid callback request",'code':400}, 
        #                 status.HTTP_400_BAD_REQUEST
        #                 )
        #     else:
        #         # Payment failed
        #         error_message = callback_data.get("message")
        #         response_data = {"status": "error", "message": error_message,'code':400}
        #         prebook.payment_status = "F"
        #         prebook.save()
        #         LOGGER.error(f"Payment Failed due to: {str(response_data)}")
        #         return Response(response_data, status.HTTP_400_BAD_REQUEST)
        # except Exception as e:
        #     response_data = {"msg": "Internal Server Error", "code": 500}
        #     LOGGER.error("Exception Occured: {}".format(str(e)))
        #     return Response(response_data,status=status.HTTP_500_INTERNAL_SERVER_ERROR)