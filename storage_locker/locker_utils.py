from django.db.models import Sum, IntegerField, Min
import requests,jwt, hashlib, base64
import json, time, datetime, os
from django.db.models import F, Case, When,Max
from datetime import datetime, timedelta
from django.utils import timezone
from utils import get_env
from django.urls import reverse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from .models import( IotRequest, 
                    BusinessInfo, 
                    Remarks, 
                    BizLkr, 
                    Book, 
                    LkrSummary,
                    Invoice,
                    Activity,
                    Employee,
                    SecurityPin,
                    BizLkrType,
                    Prebook,
                    Customer,
                    LkrStatusLog,
                    Payment,
                    BookToken
                    )
from .mqtt import publish_message
from payments.payment_utils import call_internal_api,call_qr_code_api
from decimal import Decimal
from datetime import time as tt
from .serializers import (
    BizLkrSerializer,
    BizLkrTypeSerializer,
    BookSerializer,
)

internal_url = get_env("INTERNAL_API_ENDPOINT")
payment_method = get_env("PAYMENT_METHOD")
secret_key = get_env("JWT_SECRET_KEY")
MERCHANT_ID = get_env("MERCHANT_ID")
STORE_ID = get_env("STORE_ID")
BASE_DOMAIN_URL = get_env("BASE_DOMAIN_URL")
BASE_URL = get_env("BASE_URL")
QRINIT_ENDPOINT = get_env("QRINIT_ENDPOINT")
TERMINAL_ID = get_env("TERMINAL_ID")
TRANSACTION_ENDPOINT = get_env("TRANSACTION_ENDPOINT")
MQREQUESTSUB = get_env('MQREQUESTSUB')
MQREPONSEPUB = get_env('MQREPONSEPUB')
WEBHOOK_BOOKING_ENDPOINT = get_env('WEBHOOK_BOOKING_ENDPOINT')
WEBHOOK_EXTEND_ENDPOINT = get_env("WEBHOOK_EXTEND_ENDPOINT")
WEBHOOK_RELEASE_ENDPOINT = get_env("WEBHOOK_RELEASE_ENDPOINT")
WEBHOOK_BOOKING_TOKEN = get_env('WEBHOOK_BOOKING_TOKEN')
WEBHOOK_EXTEND_TOKEN = get_env('WEBHOOK_EXTEND_TOKEN')
WEBHOOK_RELEASE_TOKEN = get_env('WEBHOOK_RELEASE_TOKEN')

def check_lkr_availability(model, biz_id, loc_id):
    lkr_summary = (
        model.objects.filter(biz=biz_id, location_id=loc_id)
        .values("status_cd")
        .annotate(avl_lkr=Sum("status_count"))
    )
    if lkr_summary:
        avail_lkr = {
            item["status_cd"]: item["avl_lkr"]
            for item in lkr_summary
            if item["status_cd"] != "B"
        }
        total_avail = avail_lkr["A"] - avail_lkr["T"]
        return total_avail
    else:
        return 0


def make_base64(json_obj):
    json_str = json.dumps(json_obj, separators=(",", ":"))  # compact encoding
    return base64.urlsafe_b64encode(bytes(json_str, "utf-8")).decode("utf-8")


def decode_data(input_str):
    data = json.loads(base64.b64decode(input_str).decode())
    return data


def make_hash(input_str):
    m = hashlib.sha256()
    m.update(input_str.encode())
    return m.hexdigest()


def generate_hash(callback_data, salt_key):
    data_to_hash = json.dumps(callback_data) + salt_key
    hashed_data = hashlib.sha256(data_to_hash.encode()).hexdigest()
    result = hashed_data + "###" + salt_key
    return result


def make_request_body(base64_payload):
    request_body = {"request": base64_payload}
    data_json = json.dumps(request_body)
    return data_json


def locker_function(BizLkr, lkr_summary, lkr_status_log, biz_id, lkr_type_id, loc_id):
    BizLkr_instance = (
        BizLkr.objects.filter(biz__id=biz_id, lkr_type__id=lkr_type_id, active_boo=1, status='A', location_id = loc_id)
        .annotate(min_updated_at=Min("updated_at"))
        .order_by("min_updated_at")
        .first()
    )
    if BizLkr_instance:
        lkr_summary.objects.filter(biz=biz_id, lkr_type_id=lkr_type_id, location_id = loc_id).update(
            status_count=Case(
                # When(status_cd="A", then=F("status_count") - 1),
                When(status_cd="B", then=F("status_count") + 1),
                When(status_cd="T", then=F("status_count") - 1),
                default=F("status_count"),
                output_field=IntegerField(),
            )
        )
        log_entry = lkr_status_log(biz_lkr=BizLkr_instance, status_cd="B")
        log_entry.save()
    return BizLkr_instance


def make_qrinit_request(salt_key_index, request_payload):
    base64_payload = make_base64(request_payload)
    verification_str = base64_payload + QRINIT_ENDPOINT + salt_key_index
    X_VERIFY = make_hash(verification_str) + "###" + salt_key_index
    url = BASE_URL + QRINIT_ENDPOINT
    data = make_request_body(base64_payload)
    headers = {
        "Content-Type": "application/json",
        "X-VERIFY": X_VERIFY,
        "X-CALLBACK-URL": BASE_DOMAIN_URL + "/api/callback/",
        "X-CALL-MODE": "POST",
    }

    response = requests.request("POST", url, headers=headers)
    return response


def get_id(model, field_name, field_value):
    instance = get_object_or_404(model, **{field_name: field_value})
    return instance.id


def make_request_payload(amount, phone_number, employee_id, prebook_id):
    request_payload = {
        "amount": amount,
        "expiresIn": 60,
        "merchantId": MERCHANT_ID,
        "storeId": phone_number,
        "terminalId": employee_id,
    }
    # Save the Prebook object to the database
    transaction_id = str(prebook_id) + "-" + datetime.now().strftime("%Y%m%d%H%M%S")
    request_payload["transactionId"] = transaction_id
    request_payload["merchantOrderId"] = prebook_id  # prebook id
    request_payload["message"] = "Payment for transaction_id: " + transaction_id

    return request_payload


def make_status_request(transaction_id, salt_key_index):
    endpoint = (
        TRANSACTION_ENDPOINT + "/" + MERCHANT_ID + "/" + transaction_id + "/status"
    )
    verification_str = endpoint + salt_key_index
    X_VERIFY = make_hash(verification_str) + "###" + salt_key_index

    url = BASE_URL + endpoint
    headers = {"Content-Type": "application/json", "X-VERIFY": X_VERIFY}

    response = requests.request("GET", url, headers=headers)
    return response


def get_prebook_data(prebook):
    cust_id = prebook.cust_id
    biz_id = prebook.biz_id
    lkr_type_id = prebook.lkr_type_id
    pay_req = prebook.pay_req_json
    return cust_id, biz_id, lkr_type_id, pay_req


def create_folder(folder):
    if not os.path.isdir(folder):
        print(folder + " not exist, hence creating it")
        os.mkdir(folder)


def make_confirmation_payload(data):
    data = {
        "type_desc": data["type_desc"],
        "amt_initial": data["amt_initial"],
        "amt_per_hr": data["amt_per_unit"],
        "min_hr": data["min_hr"],
    }
    return data


def make_endtime(data):
    start_dt = datetime.strptime(str(data["start_time"]), "%d-%b %I:%M %p")
    end_date = start_dt + timedelta(hours=data['booked_duration'])
    data["end_time"] = end_date.strftime("%-d-%b %-I:%M %p")
    return data


def CheckAvailLocker(kwargs, biz_id, Location, loc_id, lock_func, lkr_summary_model):
    token = generate_token(kwargs)
    try:
        if biz_id is not None:
            try:
                total_avail = lock_func(lkr_summary_model, biz_id, loc_id)
                data = {
                    "available_lockers": total_avail,
                    "location": Location,
                    "biz": '{}-{}'.format(biz_id, loc_id),
                }
                if token is not None:
                    booking_page_link = internal_url + "/bookingpage/" + token + "/"
                    data['token'] = token
                    data['booking_page_link'] = booking_page_link
                response_data = response_builder("Total No of Available_Lockers",data,'success',200)
            except lkr_summary_model.DoesNotExist:
                data = {
                    "biz": biz_id, 
                    "location_id": loc_id,
                }
                response_data = response_builder("LkrSummary not found",data,'failed',404)
        else:
            response_data = response_builder("biz_id does not exist",{"biz":biz_id},'failed',400)
    except Exception as e:
        response_data = response_builder("Internal server error",str(e),'failed',500)
    return response_data


def calculate_total_time(booked_time):

    cur_timestamp = datetime.now().replace(tzinfo=None)
    cur = cur_timestamp - (booked_time).replace(tzinfo=None)
    total_seconds = cur.total_seconds()
    days = cur.days
    hours = (total_seconds % (24 * 3600)) // 3600
    minutes = (total_seconds % 3600) // 60
    hours = hours + 1 if int(minutes) > 0 else hours
    return days, hours, minutes

def build_mqtt_payload(biz_id, locker_id):
    # request_id get the greatest id from the iot_request_Table and add 1 to it.
    # locker_no =  Book Table, biz_lckr_id
    max_req_id = (
        IotRequest.objects.filter(biz=biz_id).aggregate(Max("req_id"))["req_id__max"]
        + 1
    )
    biz_instance = BusinessInfo.objects.get(pk=biz_id)
    iot_cli_id = biz_instance.iot_client_id
    cur_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = """{{
        "from": "server.12345",
        "to": '{}',
        "topic": "RTA",
        "content": {{
            "request_id": "{}",
            "action": "Open", 
            "locker_no": "{}"
        }},
        "timestamp": "{}"
    }}""".format(
        iot_cli_id, max_req_id, locker_id, cur_timestamp
    )
    return eval(payload), biz_instance

def create_dict(**kwargs):
    return kwargs

def PublishSend(payload, biz_instance, logger):
    request_id=payload['content']['request_id']
    new_request = IotRequest(
        biz=biz_instance,
        req_id=request_id,
        type=payload['topic'],
        request_json=payload,
        response_json='',
        status='Pending',
    )
    new_request.save()
    pk = new_request.pk
    publish_message(MQREQUESTSUB, json.dumps(payload))
    Iot = IotRequest.objects.get(pk=pk)
    if Iot.status == "Pending":
        pending_count = 0
        while pending_count < 20:
            time.sleep(1)
            Iot = IotRequest.objects.get(pk=pk)
            if Iot.status == "success":
                break
            pending_count += 1
        if Iot.status == "Pending" and Iot.response_json is None:
            Iot.status = "ERROR" 
            Iot.save()
        response_data = {"message": "Internal Server Error", "code": 500}
    if Iot.remarks is not None:
        rem_id = Iot.remarks
        iot_res_req_id = Iot.response_json["content"]["request"]["request_id"]
        rem_inst = Remarks.objects.get(pk=rem_id)
        logger.warning(
            "There is an duplicate Request ID: {} for the Issue {}".format(
                str(rem_id), rem_inst.remarks
            )
        )
        max_req_id = request_id + 2
        if iot_res_req_id > max_req_id:
            max_req_id = iot_res_req_id
        payload['content']['request_id'] = max_req_id
        PublishSend(payload, biz_instance, logger)
    if Iot.status == "ERROR":
        counter = 0
        while counter < 2:
            time.sleep(5)
            PublishSend(payload, biz_instance, logger)
            Iot = IotRequest.objects.get(pk=pk)
            if Iot.status == "success":
                break
            counter += 1
        response_data = {"message": "Internal Server Error", "code": 500}
    if Iot.status == "success":
        response_data = {"message": "success", "code": 200}
    return response_data

def totaltime(book):
    days, hours, minutes = calculate_total_time(book.start_dt)
    total_hours = (days * 24) + hours
    total_time_str = f"{total_hours:.2f} hours"
    return total_time_str


def Invoice_Gen(cus, book, lock_no, loc_name):
    days, hours, minutes= calculate_total_time(book.start_dt + timedelta(hours=5, minutes=30))
    duration = timedelta(days=days, hours=hours, minutes=minutes)
    biz_lkr = BizLkr.objects.get(pk=book.biz_lkr_id)
    amount = calculate_amount_in_units(int(hours),book.biz_id,
            biz_lkr.lkr_type_id,book.location_id,False,days)['amount']
    biz_lkr_type = BizLkrType.objects.get(pk=biz_lkr.lkr_type_id)
    cus_ins = Customer.objects.get(pk=cus.id)
    balance_amount = amount - book.advance_amt if amount - book.advance_amt > 0 else 0
    prebook = Prebook.objects.get(pk=book.pbook_id)
    # 1 day(s) 5 hr(s) 36 min(s) 
    total_time = f"{days} day(s) {hours} hr(s) {minutes} min(s)" if days > 0 else f"{hours} hr(s) {minutes} min(s)"
    payload = {
        "lock_no": lock_no,
        "booking_id": prebook.reference_id,
        "size":biz_lkr_type.type_desc,
        "total_hour_booked":book.booked_duration.total_seconds() / 3600,
        "location": loc_name,
        "duration":{
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "duration_str": total_time
            },
        "amount_paid":float(book.advance_amt),
        "balance_amount": float(balance_amount),
        "total_amount": float(book.advance_amt + balance_amount),
        "start_time": to_datetime(str(book.start_dt + timedelta(hours=5, minutes=30))),
        "end_time": to_datetime(str(book.end_dt)),
        }
    inv_instance = Invoice(
        name= cus_ins.name,
        phone_no = cus_ins.prim_no,
        location = loc_name,
        lock_no = lock_no,
        duration = duration,
        initial_amt = biz_lkr_type.amt_initial,
        total_amt = balance_amount,
        transaction_id = book.id,
        customer_id = cus.id
        )
    inv_instance.save()
    return payload

def locker_release(lock_no, biz_id, book_id,loc_id, LOGGER):
    response = {"status": "success"}
    try:
        obj = get_object_or_404(BizLkr,lock_no=lock_no, biz_id=biz_id, location_id = loc_id)
        obj.status = 'A'
        obj.save()
        book_ins = get_object_or_404(Book,pk=book_id)
        book_ins.active_boo = 0
        # update duration feild, total lock fee
        book_ins.end_dt = datetime.now()
        book_ins.save()
        LkrSummary.objects.filter(lkr_type_id=obj.lkr_type_id, biz_id=biz_id, location_id = loc_id).update(
                status_count=Case(
                    When(status_cd="A", then=F("status_count") + 1),
                    When(status_cd="B", then=F("status_count") - 1),
                    # When(status_cd="T", then=F("status_count") - 1),
                    default=F("status_count"),
                    output_field=IntegerField(),
                )
            )
    except Exception as e:
        response['status'] = "failed"
        LOGGER.error("Error Updating tables due to {}".format(e))
    return response

def calculate_amount(booking_hrs, biz_id, locker_type_id, loc_id, days=0):
    try:
        if ':' in str(booking_hrs):
            booking_hrs = int(booking_hrs.split(":")[0])
        lkr_type_instance = BizLkrType.objects.get(pk=locker_type_id, location_id=loc_id, biz_id=biz_id)
        amt_per_hr = lkr_type_instance.amt_per_unit
        processing_fee = lkr_type_instance.processing_fee
        days_amount = days * lkr_type_instance.max_24_amt
        hrs_amount = (int(booking_hrs) * amt_per_hr) + processing_fee
        if int(hrs_amount) > lkr_type_instance.max_24_amt:
            hrs_amount = lkr_type_instance.max_24_amt
        totalAmount = days_amount + hrs_amount
        data = {"amount": totalAmount,'status':True}
        return data
    except BizLkrType.DoesNotExist:
        return {"status": False, 
            'msg':'There are no lockers matching your combination of lockertype, biz_id and location_id',
            'code':400}
    except Exception as e:
        return {"status": False, 'msg':str(e),'code':500}

def calculate_amount_in_units(booking_hrs, biz_id, locker_type_id, loc_id, extend, days=0):
    try:
        lkr_type_instance = BizLkrType.objects.get(pk=locker_type_id, location_id=loc_id, biz_id=biz_id)
        unit = lkr_type_instance.units  
        amt_initial = lkr_type_instance.amt_initial  
        min_hr = lkr_type_instance.min_hr
        amt_per_unit = lkr_type_instance.amt_per_unit
        processing_fee = lkr_type_instance.processing_fee
        if unit == "hour":
            days_amount = days * lkr_type_instance.max_24_amt
            hrs_amount = amt_initial + ((Decimal(booking_hrs) - min_hr) * amt_per_unit)
            if not extend:
                hrs_amount = hrs_amount + processing_fee
            if int(hrs_amount) > lkr_type_instance.max_24_amt:
                hrs_amount = lkr_type_instance.max_24_amt
            totalAmount = days_amount + hrs_amount
            data = {"amount": totalAmount}
            return data
        if unit == "day":
            min_day = min_hr/24
            days_amount = amt_initial + ((days - min_day) * amt_per_unit)
            if not extend:
                days_amount = days_amount + processing_fee
            totalAmount = days_amount
            data = {"amount": totalAmount}
            return data        
        if unit == "month":
            min_month = min_hr/720
            month_amount = amt_initial + ((booking_hrs - min_month) * amt_per_unit)
            if not extend:
                month_amount = month_amount + processing_fee
            totalAmount = month_amount
            data = {"amount": totalAmount}
            return data
    except BizLkrType.DoesNotExist as err:
        raise Exception("Error due to", repr(err))
    except Exception as e:
        raise Exception("Error due to", repr(e))

def update_activity(book_id, status, user_id, biz_id, loc_id, cust_id):
    print(book_id, status, user_id, biz_id, loc_id, cust_id)
    if status == 'prebook':
        lock_no,book_id = None,None
    else:
        book = Book.objects.get(pk=book_id)
        biz_lkr = BizLkr.objects.get(pk=book.biz_lkr_id)
        lock_no = biz_lkr.lock_no
    new_activity = Activity(
    biz_id=biz_id,
    loc_id=loc_id,
    book_id=book_id,
    cus_id=cust_id,
    lock_no=lock_no,
    activity_status=status, 
    emp_id=user_id,
    created_at=datetime.now()  
    )
    new_activity.save()

def booking(customer_instance,biz_instance,biz_lkr_instance,
    prebook_id, sec_pin_id, amount, pay_req, 
    pay_res, booked_duration,loc_id, emp_id):
    new_book = Book(
        cust=customer_instance,
        biz=biz_instance,
        biz_lkr=biz_lkr_instance,
        pbook_id=prebook_id,
        sec_pin_id=sec_pin_id,
        security_block="N",
        start_dt=datetime.now(),
        active_boo=1,
        advance_amt=amount,
        pay_req_json=pay_req,
        pay_res_json=pay_res,
        booked_duration=booked_duration,
        location_id = loc_id,
        emp_id =emp_id,
    )
    new_book.save()
    biz_lkr_instance.status = 'U'
    biz_lkr_instance.save()

    return new_book, new_book.id


def ZeroAmountPayload(prebook_id,booked_duration,transactionId)-> dict:
    payload = {
        "success": True,
        "code": "PAYMENT_SUCCESS",
        "prebook_id": prebook_id,
        "data": {
            "amount": 0.0,
            "booked_duration": booked_duration,
            "transactionId": transactionId,
        },
    }
    return json.dumps(payload)

def SendBookingRequest(request,payload,UrlName)-> dict:
    url  = internal_url + reverse(UrlName)
    token = request.headers.get('Authorization')
    headers = {"Content-type": "application/json", 'Authorization': token}
    response = requests.post(url,data=payload, headers=headers).json()
    return response

def SaveSecurityInstance(prebook_instance, phone_number, pin):
    security_pin = SecurityPin(
        sec_pin_pbook=prebook_instance,
        sec_pin_mobile_no=phone_number,
        sec_pin_pin=make_hash(str(pin)),
    )
    security_pin.save()

def BookInfoPayload(book_data, cus_instance):
    biz_lkr = BizLkr.objects.get(pk=book_data.biz_lkr_id)
    lkr_type_id = biz_lkr.lkr_type_id
    # hour = calculate_total_time(book_data.end_dt)
    # print(hour)
    payload = {
        "book_id":book_data.id,
        "phone_no":cus_instance.prim_no,
        'locker_id':biz_lkr.id,
        'locker_no':biz_lkr.lock_no,
        "biz":'{}-{}'.format(book_data.biz_id, book_data.location_id),
        "lkr_type_id":biz_lkr.lkr_type_id,
        "booked_time":to_hr_format(book_data.start_dt),
        "end_time":to_hr_format(book_data.end_dt),
        "booked_duration": book_data.booked_duration / 3600,
        # 'incremental_units' : generate_numbers('min_hr','max_hr','increment_units'),
        "security_block":book_data.security_block,
        "advance_amount":book_data.advance_amt,
        "total_fee":book_data.tot_lock_fee,
        "actual_duration": book_data.duration,
        "active_book":book_data.active_boo
        }
    return payload

def GetUserType(request):
    try:
        emp = Employee.objects.get(user_id=request.user.id)
    except Employee.DoesNotExist:
        return   response_builder("Unsuccessful response data",
                                             {"user_id":request.user.id},'failed', 400 )
    return emp.usertype
def generate_numbers(min_hr, max_hr, increment_units):
    return list(range(min_hr, max_hr + 1, increment_units))


def locker_booking(json_payload, logger):
    try:
        payload = json.loads(json_payload)
        success = payload.get("success")
        code = payload.get("code")
        transaction_id = payload.get("data", {}).get("transactionId","")
        prebook_id = transaction_id[1:-14]
        booked_duration =  payload.get("data", {}).get("booked_duration","")
        try:
            book = Book.objects.get(pbook_id=prebook_id)
            response_data = response_builder("Locker already booked for this Prebook ID",{},"failed",400)
            logger.info("Locker already booked for this Prebook ID {}".format(prebook_id))
        except:
            pass
        prebook = Prebook.objects.get(pk=prebook_id)
        loc_id = prebook.location_id
        if success and code == "PAYMENT_SUCCESS":
            # Payment successful
            amount = payload.get("data", {}).get("amount")
            try:
                prebook.payment_status = "P"
                prebook.save()
                sec_pin_id = SecurityPin.objects.values_list("pk", flat=True).get(
                    sec_pin_pbook_id=prebook_id
                )
                cust_id, biz_id, lkr_type_id, pay_req = get_prebook_data(prebook)
                customer_instance = Customer.objects.get(pk=cust_id)
                biz_instance = BusinessInfo.objects.get(pk=biz_id)
                biz_lkr_instance = locker_function(BizLkr, LkrSummary, LkrStatusLog, biz_id, lkr_type_id, loc_id)
                if biz_lkr_instance is None:
                    response_data = response_builder("Currently there are no lockers  available",{},"failed",204)
                else:
                    book_id =  booking(customer_instance,biz_instance,biz_lkr_instance,
                                prebook_id, sec_pin_id, amount, pay_req, 
                                payload, booked_duration,loc_id)
                    data = {"book_id":book_id}
                    response_data = response_builder("Locker Booked SuccessFully",data,"success",200)
            except Exception as e:
                logger.error("Booking failed due to {}". format(e))
                prebook.payment_status = "F"
                prebook.save()
                response_data = response_builder("Invalid callback request",{},"failed",400)
        else:
            error_message = payload.get("message")
            logger.error("Booking failed due to {}". format(error_message))
            response_data = response_builder(error_message,payload,"failed", 400)
            prebook.payment_status = "F"
            prebook.save()
    except Exception as e:
        logger.error("Unexpected Error Occured due to {}". format(e))
        response_data = response_builder("Internal Server Error",{},"failed", 500)
    return response_data

# message,data,status,code

def response_builder(msg,data,status,code):
    # if data:
    #     data = [data]
    response = {
        "msg":str(msg),
        "data":data,
        "status":status,
        "code":code
    }
    return response

def send_response(response, logger):
    status_codes = {
        200: status.HTTP_200_OK,
        201: status.HTTP_201_CREATED,
        202: status.HTTP_202_ACCEPTED,
        204: status.HTTP_204_NO_CONTENT,
        306: status.HTTP_306_RESERVED,
        400: status.HTTP_400_BAD_REQUEST,
        401: status.HTTP_401_UNAUTHORIZED,
        402: status.HTTP_402_PAYMENT_REQUIRED,
        403: status.HTTP_403_FORBIDDEN,
        404: status.HTTP_404_NOT_FOUND,
        412: status.HTTP_412_PRECONDITION_FAILED,
        500: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    code = response["code"]
    if code in status_codes:
        status_value = status_codes[code]
        logger_msg = "{} : {}".format(response["msg"], response["data"])
        logger_func = logger.info if code < 300 else (logger.warn if code < 400 else logger.error)
        # logger_func = logger.info if code < 400 else logger.error
        logger_func(logger_msg)
        return Response(response, status=status_value)
    else:
        # Handle default case or raise an exception
        logger.error("Unhandled response code: {}".format(code))
        return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def open_locker_response(lock_no, invoice, amount, booking_info, est_endtime):
    estimated_end_time = make_endtime(est_endtime)['end_time']
    resp = {
        "locker_no":lock_no,
        "amount":float(amount),
        "estimated_end_time":estimated_end_time,
        "invoice":invoice,
        "payment_details":booking_info
        }
    return resp

def to_datetime(date_str):
    if date_str is None or date_str == "None": return None
    d = datetime.fromisoformat((str(date_str)))
    date_time = d.strftime("%-d-%b %-I:%M %p")
    return date_time

def get_payment_link_or_estimate(request , payment_link, 
    booking_id,booking_hrs, biz_id, lkr_type_id, loc_id, intent,reference_id_type, days=0, hour=None):
    if booking_id is not None:
        try:
            bookdata = Book.objects.get(pk=booking_id)
            customer = Customer.objects.get(pk=bookdata.cust_id)
            biz_lkr = BizLkr.objects.get(pk=bookdata.biz_lkr_id)
            lkr_type_id = biz_lkr.lkr_type_id
            reference_id = (
                "B" + str(booking_id) + datetime.now().strftime("%Y%m%d%H%M%S") + str(request.user.id)
            )
            prev_booked_hrs = bookdata.booked_duration.total_seconds() // 3600
            if hour == None:
                hour = prev_booked_hrs + booking_hrs
            total_hr = prev_booked_hrs + booking_hrs
            booked_duration = str(tt(booking_hrs, 0))
            start_time = bookdata.start_dt + timedelta(hours=5, minutes=30)
            cur_end_time = to_hr_format(start_time + timedelta(hours=prev_booked_hrs))
            end_time = to_hr_format(start_time + timedelta(hours=total_hr))
            startdt = to_hr_format(start_time)
            resp = calculate_amount_in_units(hour, biz_id, lkr_type_id, loc_id, False, days)
            bal_amt = resp['amount'] - bookdata.advance_amt
            print("Balance Amount::::", bal_amt)
            amount_paid = bookdata.advance_amt
            payload = {
                    'start_time': startdt,
                    "current_end_time":cur_end_time,
                    "expected_end_time": end_time,
                    "booked_hrs":prev_booked_hrs,
                    "extended_hours":booking_hrs,
                    "amount_paid": float(amount_paid),
                    "amount_to_pay": bal_amt,
                    "locker_no": biz_lkr.lock_no,
                    }
            if amount_paid  == 0 and intent == 'Extend':
                payload['amount_to_pay'] = 0
                payload['payment_info'] = {}
                bookdata.booked_duration = bookdata.booked_duration + timedelta(hours=booking_hrs)
                bookdata.save()
                update_activity(bookdata.id, "Extend", request.user.id, biz_id, loc_id, customer.id)
                response_data = response_builder("successful response data",
                        payload,'success', 201 )
                # print("********************************")
                # print(response_data)
                # emp = Employee.objects.get(user_id=request.user.id)
                # user = emp.usertype
                # if user == 'WhatsApp':
                #     calling_webhook(response_data, bookdata.cust_id, 'extend')
                # print("********************************")
                return response_data
            # Sending normal response only when the amount less than zero
            if bal_amt <= 0:
                data = calculate_amount_in_units(hour, biz_id, lkr_type_id, loc_id, False, days)
                print("Amount:::::", data['amount'])
                response_data = response_builder("Successful response",
                            {"amount": data['amount']},'success', 200 )
                return response_data
        except BizLkr.DoesNotExist:
            response_data = response_builder("There are no lockers available for this locker id",
                                             {"locker_id": bookdata.biz_lkr_id},'failed', 400 )
            return response_data
        except Customer.DoesNotExist:
            response_data = response_builder("There is no customer exist for the customer id",
                                             {"customer_id": bookdata.cust_id},'failed', 400 )
            return response_data
        except Prebook.DoesNotExist:
            response_data = response_builder("There is no prebook available for the prebook id",
                                             {"prebook_id": bookdata.pbook_id},'failed', 400 )
            return response_data
        except Book.DoesNotExist:
            response_data = response_builder("There is no booking available for the booking id",
                                             {"booking_id": booking_id},'failed', 400 )
            return response_data
        if payment_link:
            userType = GetUserType(request)
            amount_p = bal_amt * 100
            data = create_dict(
                amount=amount_p, contact=customer.prim_no, reference_id=reference_id, 
                booked_duration=total_hr 
            )
            print("data:::", data)
            bookdata.book_ref_id = reference_id
            
            bookdata.save()
            # if userType == 'WhatsApp':
            request_payload, response = call_internal_api(request, data, intent, reference_id_type)
            print("response:::", response)
            try:
                response['data']['amount'] = response['data']['amount'] / 100
                response['data']['short_url'] = response['data'].pop("payLink")
                response['data']['upi'] = response['data'].pop("upiIntent")
                response['data']['token'] = response['data']['short_url'].rsplit("/")[-1]
                AddPaymentEntry(biz_id,loc_id,booking_id,reference_id,
                reference_id_type,bal_amt,intent, request_payload,booked_duration,bookdata.cust_id)
            except:
                if response['success'] is False:
                    response_data = response_builder("Unsuccessful response data",
                                            response,'failed', 400 )
                    return response_data
            # else:
            #     request_payload, response = call_qr_code_api(request, data)
            #     try:
            #         response['amount'] = response['payment_amount'] / 100
            #         del response['payment_amount']
            #     except:
            #         if response['success'] is False:
            #             response = response_builder(
            #                 "Unsuccessful response data",
            #                 response,'failed', 400 )
            #             return response
            payload['payment_info'] = response
            bookdata.pay_req_json = request_payload
            bookdata.pay_res_json = response
            bookdata.save()
            response_data = response_builder("successful response data",
                                    payload,'success', 201 )
            return response_data
        else:
            resp['amount'] = bal_amt
            response_data = response_builder("successful response data",
                                    resp,'success', 200 )
            return response_data
    else:
        data = calculate_amount_in_units(booking_hrs, biz_id, lkr_type_id, loc_id, False)
        response_data = response_builder("successful response data",
                                data,'success', 200 )
        return response_data
    
def get_booking_info(estimation, invoice, prebook):
    try:
        if estimation['code'] == 201:
            booking_info = {}
            booking_info['amount_paid'] = estimation['data']['amount_paid']
            booking_info['balance_amount'] = estimation['data']['payment_info']['data']['amount']
            booking_info['upi'] = estimation['data']['payment_info']['data']['upi']
            booking_info['short_url'] = estimation['data']['payment_info']['data']['short_url']
            prebook.save()
        else:
            booking_info = estimation['data']
    except KeyError as err:
        booking_info = {"error": str(err)}
    return booking_info

def get_booking_fields(prebook):
    pid = prebook.id
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
    return sec_pin_id, customer_instance,biz_instance,biz_lkr_instance

def GetWebhookUrlAndHeaders(reason):
    if reason == 'book':
        url=WEBHOOK_BOOKING_ENDPOINT
        token = WEBHOOK_BOOKING_TOKEN
    elif reason == 'extend':
        url = WEBHOOK_EXTEND_ENDPOINT
        token = WEBHOOK_EXTEND_TOKEN
    else:
        url = WEBHOOK_RELEASE_ENDPOINT
        token = WEBHOOK_RELEASE_TOKEN
    return url, token

def calling_webhook(data, cust_id, reason):
    cust = Customer.objects.get(pk=cust_id)
    data['mobile_no'] = "91" + str(cust.prim_no)
    url, token = GetWebhookUrlAndHeaders(reason)
    json_data = json.dumps(data)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    response = requests.post(url, data=json_data, headers=headers)
    return response.json()

def to_hr_format(time):
    # total_hr = time.total_seconds() // 3600
    if time is None or time == "None": return None
    total_hr = time.strftime("%-d-%b %-I:%M %p")
    return total_hr

def AddPaymentEntry(biz_id,loc_id,book_id,
    reference_id,ref_id_type,amount, intent, req_json, booking_hrs,cust_id):
    payment = Payment(
    payment_gateway=payment_method,
    payment_type='UPI',
    biz_id=biz_id,
    loc_id=loc_id,
    book_id=book_id,
    cust_id=cust_id,
    payment_status='O',
    extended_duration=booking_hrs,
    ref_id=reference_id,
    ref_id_type=ref_id_type,
    amount=amount,  
    intent=intent,
    pay_req=req_json, 
    added_dt=timezone.now(),
)
    payment.save()

def confirm_api_response(prebookid,Prebook_serializer ):
    book_instance = Book.objects.get(pbook=prebookid)
    book_data = BookSerializer(book_instance).data
    biz_lkr = BizLkr.objects.get(pk=book_data["biz_lkr"])
    biz_lkr_data = BizLkrSerializer(biz_lkr).data
    biz_lkr_type = BizLkrType.objects.get(pk=Prebook_serializer["lkr_type"])
    biz_lkr_type_data = BizLkrTypeSerializer(biz_lkr_type).data
    response_data = make_confirmation_payload(biz_lkr_type_data)
    response_data["amount_paid"] = float(book_data["advance_amt"])
    response_data["booking_id"] = book_data["id"]
    response_data["lock_no"] = biz_lkr_data["lock_no"]
    response_data["start_time"] = to_datetime(book_data['start_dt'])
    response_data["booked_duration"] = book_instance.booked_duration.seconds // 3600
    response_data = make_endtime(response_data)
    response = response_builder("Locker allocated succesfully",response_data,'success',200)
    return response

def generate_token(kwargs):
    try:
        expiration_time = datetime.utcnow() + timedelta(minutes=10)
        payload = {'exp': expiration_time,'biz':kwargs['pk'],'mn':kwargs['mn']}
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token
    except:
        return None

def is_valid_booking_token(token):
    try:
        if token is None:
            return None
        # Decode the token
        payload = jwt.decode(token,secret_key, algorithms=['HS256'])
        # Check if the token is expired
        if datetime.utcnow() > datetime.utcfromtimestamp(payload['exp']):
            return {"status":False}
        # Continue with rendering the booking page
        return {"status":True, 'payload':payload}
    except jwt.ExpiredSignatureError:
        return {"status":False}
    except jwt.InvalidTokenError:
        return {"status":False}
    

def update_book_token(booking_token,prebook_id):
    if booking_token is not None:
        token = BookToken.objects.get(token=booking_token)
        token.pbook = prebook_id
        token.status = 1
        token.expired_at = timezone.now()
        token.save()
