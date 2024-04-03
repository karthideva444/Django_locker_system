from utils.get_env_utils import get_env
from payments.payment_utils import decode_base64
import json

payment_method = get_env("PAYMENT_METHOD")

def PaymentGatewayResponse(response, amount):
    if payment_method == "phonepe":
        response = phonepe_response(response)
        return response
    if payment_method == "phonepeV1":
        response = phonepeV1_response(response, amount)
        return response

def phonepe_response(json_response):
    data = json_response.get("data", None)
    amount = data.get("amount", None)
    reference_id = data.get("transactionId", None)
    contact = data.get("mobileNumber", None)
    payment_id = data.get("upiIntent", None)
    short_url = data.get("payLink", None)
    token = None
    if short_url is not None:
        token =short_url.rsplit("/")[-1]
    response_dict = {
        "amount": amount // 100,
        "currency": "INR",
        "reference_id": reference_id,
        "locker_type_id": None,
        "contact": contact,
        "payment": True,
        "payment_details": {
            "upi": payment_id,
            "short_url": short_url,
            "token":token
        },
    }
    return response_dict


def phonepeV1_response(json_response, amount):
    data = json_response.get("data", None)
    if data is not None:
        reference_id = data.get("merchantTransactionId", None)
        pay_link = data["instrumentResponse"]["redirectInfo"]["url"]
        response_dict = {
            "amount": amount,
            "currency": "INR",
            "reference_id": reference_id,
            "locker_type_id": None,
            "payment": True,
            "payment_details": {
                "short_url": pay_link,
            },
        }
        return response_dict
    return {}

def zero_payment_response(data):
    amount = data.get("amount", None)
    reference_id = data.get("reference_id", None)
    contact = data.get("contact", None)
    response_dict = {
        "amount": amount,
        "currency": "INR",
        "reference_id": reference_id,
        "locker_type_id": None,
        "contact": contact,
        "payment": False,
        "payment_details": {
            "upi": None,
            "short_url": None,
        },
    }
    return response_dict

def build_callback_response(response):
    if payment_method == "phonepeV1":
        decoded_response = decode_base64(response)
        if decoded_response['success'] == True:
            reference_id = decoded_response['data']['merchantTransactionId']
            prebookid, initiated_by = reference_id, reference_id[-1]
            return prebookid, initiated_by, decoded_response
        return (None, None, decoded_response)