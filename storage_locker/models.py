# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
  # * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import User
from django.db.models import UniqueConstraint


class Activity(models.Model):
    book_id = models.IntegerField(blank=True, null=True)
    biz_id = models.IntegerField(blank=True, null=True)
    cus_id = models.IntegerField(blank=True, null=True)
    emp_id = models.IntegerField(blank=True, null=True)
    loc_id = models.IntegerField(blank=True, null=True)
    lock_no = models.CharField(max_length=10, blank=True, null=True)
    activity_status = models.CharField(max_length=20, blank=True, null=True, db_comment='Either Opened or Booked or Paid or Released')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'activity_log'
    
class BizAccessType(models.Model):
    biz = models.ForeignKey('BusinessInfo', models.DO_NOTHING)
    access_type = models.CharField(max_length=60)

    class Meta:
        # managed = False
        db_table = 'biz_access_type'


class BizLkr(models.Model):
    biz = models.ForeignKey('BusinessInfo', models.DO_NOTHING)
    lock_no = models.IntegerField()
    lkr_type = models.ForeignKey('BizLkrType', models.DO_NOTHING)
    lkr_catalog = models.ForeignKey('LkrCatalog', models.DO_NOTHING)
    location = models.CharField(max_length=50, blank=True, null=True, db_comment='M/F')
    tier_no = models.IntegerField(blank=True, null=True)
    row_no = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=1, blank=True, null=True, db_comment='In-Use(U) or Reserved(R) or Blocked for Payment(B) or Available (A) , Maintenance (M)')
    added_dt = models.DateField(blank=True, null=True, auto_now_add= True)
    end_dt = models.DateField(blank=True, null=True)
    active_boo = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True,auto_now=True)
    location_id = models.IntegerField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'biz_lkr'


class BizLkrType(models.Model):
    biz = models.ForeignKey('BusinessInfo', models.DO_NOTHING)
    type_desc = models.CharField(max_length=50, blank=True, null=True)
    det_desc = models.TextField(blank=True, max_length=500,null=True)
    amt_initial = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    min_hr = models.IntegerField(blank=True, null=True)
    amt_per_unit = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    image_url = models.CharField(max_length=512, blank=True, null=True)
    added_date = models.DateField(blank=True, null=True, auto_now_add= True)
    processing_fee = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    max_24_amt = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    location_id = models.IntegerField(blank=True, null=True)
    units = models.CharField(max_length=10, blank=True, null=True)
    increment_units = models.IntegerField(blank=True, null=True)
    max_hr = models.IntegerField(blank=True, null=True)
    class Meta:
        # managed = False
        db_table = 'biz_lkr_type'

class BizLocation(models.Model):
    location_id = models.IntegerField(blank=True, null=True, unique=True)
    biz_id = models.IntegerField(blank=True, null=True)
    biz_info = models.ForeignKey('BusinessInfo', models.DO_NOTHING)
    loc_name = models.CharField(max_length=50, blank=True, null=True)
    device_name = models.CharField(max_length=50, blank=True, null=True)
    comments =  models.CharField(max_length=512, blank=True, null=True)
    class Meta:
        # managed = False
        db_table = 'location'

class Book(models.Model):
    cust = models.ForeignKey('Customer', models.DO_NOTHING)
    biz = models.ForeignKey('BusinessInfo', models.DO_NOTHING)
    biz_lkr = models.ForeignKey(BizLkr, models.DO_NOTHING)
    booked_duration = models.DurationField(blank=True, null=True)
    book_ref_id =  models.CharField(max_length=45, blank=True, null=True)
    emp_id = models.IntegerField(blank=True, null=True)
    pbook = models.ForeignKey('Prebook', models.DO_NOTHING)
    sec_pin = models.ForeignKey('SecurityPin', models.DO_NOTHING)
    security_block = models.CharField(max_length=1, blank=True, null=True, db_comment='Defaulted to N, if customer enters pin incorrectly 3 times, it wil be set to Y. and can only be updated by Admin to N after changing the sec_pin')
    start_dt = models.DateTimeField(blank=True, null=True)
    end_dt = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True, db_comment='Calcualted when end dt is populated \n')
    active_boo = models.IntegerField(blank=True, null=True)
    advance_amt = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    tot_lock_fee = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    oth_chrgs = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    pay_req_json = models.JSONField(blank=True, null=True)
    pay_res_json = models.JSONField(blank=True, null=True)
    added_dt = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    updated_dt = models.DateTimeField(blank=True, null=True, auto_now= True)
    location_id = models.IntegerField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'book'


class BusinessInfo(models.Model):
    name = models.CharField(max_length=90, blank=True, null=True)
    address_1 = models.CharField(max_length=255, blank=True, null=True)
    address_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=45, blank=True, null=True)
    state = models.CharField(max_length=45, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    location = models.TextField(blank=True, null=True, db_comment='Geo location ')  # This field type is a guess.
    contact_1 = models.CharField(max_length=10, blank=True, null=True)
    contact_2 = models.CharField(max_length=10, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True, db_comment='Free Text\n')
    added_date = models.DateField(blank=True, null=True, auto_now_add= True)
    end_date = models.DateField(blank=True, null=True)
    active_boo = models.IntegerField(blank=True, null=True)
    loc_id = models.IntegerField(blank=True, null=True)
    loc_name = models.CharField(max_length=50,blank=True, null=True)
    iot_client_id = models.CharField(max_length=50,blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'business_info'


class CodeTable(models.Model):
    code_id = models.IntegerField(primary_key=True)  # The composite primary key (code_id, code) found, that is not supported. The first column is selected.
    code = models.CharField(max_length=20)
    code_description = models.CharField(max_length=60, blank=True, null=True)
    code_active = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'code_table'
        unique_together = (('code_id', 'code'),)


class CommTemplate(models.Model):
    name = models.CharField(max_length=50)
    content = models.TextField()

    class Meta:
        # managed = False
        db_table = 'comm_template'


class Customer(models.Model):
    name = models.CharField(max_length=60, blank=True, null=True)
    prim_no = models.CharField(max_length=10, blank=True, null=True)
    alt_no = models.CharField(max_length=10, blank=True, null=True)
    cust_comm_mode = models.CharField(max_length=1, blank=True, null=True)
    cust_enroll_dt = models.DateTimeField(blank=True, null=True, auto_now_add= True)

    class Meta:
        # managed = False
        db_table = 'customer'


class CustomerCommunication(models.Model):
    comm_id = models.IntegerField(primary_key=True)
    comm_cust = models.ForeignKey(Customer, models.DO_NOTHING)
    comm_in_out = models.CharField(max_length=1, blank=True, null=True)
    comm_dt = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    comm_mode = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'customer_communication'

class ChangeLog(models.Model):
    biz_id = models.IntegerField()
    loc_id = models.IntegerField()
    cu_id = models.CharField(max_length=3)
    status = models.CharField(max_length=100, null=True, default=None)
    locker_no = models.IntegerField(null=True, default=None)
    lock_status = models.CharField(max_length=1, null=True, default=None, help_text="O(Open) or C(Close)")
    ir_status = models.CharField(max_length=45, null=True, default=None)
    added_dt = models.DateTimeField(null=True, default=None)
    class Meta:
        # managed = False
        db_table = 'change_log'

class CuCmd(models.Model):
    cu_id = models.CharField(max_length=3)
    biz_id = models.IntegerField()
    loc_id = models.IntegerField()
    status_cmd = models.CharField(max_length=12)
    class Meta:
        # managed = False
        constraints = [
            UniqueConstraint(fields=['cu_id', 'biz_id','loc_id'], name='cu_cmd_pk')
        ]
        db_table = 'cu_cmd'
class Employee(models.Model):
    name = models.CharField(max_length=60, blank=True, null=True)
    role = models.CharField(max_length=60)
    user = models.ForeignKey(User, models.DO_NOTHING)
    biz = models.IntegerField(blank=True, null=True)
    mobile_no = models.CharField(max_length=10)
    alt_no = models.CharField(max_length=10, blank=True, null=True)
    email_id = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=256)
    pass_updated_dt = models.DateTimeField(blank=True, null=True)
    pass_expiry_dt = models.DateTimeField(blank=True, null=True)
    address_1 = models.CharField(max_length=255, blank=True, null=True)
    address_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=45, blank=True, null=True)
    state = models.CharField(max_length=45, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    added_dt = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    active_boo = models.IntegerField()
    usertype = models.CharField(max_length=45, blank=True, null=True)
    location_id = models.IntegerField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'employee'

class Invoice(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    phone_no = models.CharField(max_length=10, blank=True, null=True)
    customer = models.ForeignKey('Customer', models.DO_NOTHING)
    location = models.CharField(max_length=30, blank=True, null=True)
    lock_no = models.CharField(max_length=10, blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    initial_amt = models.DecimalField(max_digits=10, decimal_places=2)
    total_amt = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'invoice'


class InstrumentBiz(models.Model):
    inst_id = models.IntegerField(primary_key=True)
    inst_biz = models.ForeignKey(BusinessInfo, models.DO_NOTHING)
    inst_type = models.CharField(max_length=45, blank=True, null=True, db_comment='Access Controller\nLocker Controller\nLock\nServer\nModem\nRepeater\nController\nRFID Tag')
    inst_rfid = models.CharField(max_length=200, blank=True, null=True)
    inst_description = models.CharField(max_length=100, blank=True, null=True)
    inst_added_date = models.DateField(blank=True, null=True, auto_now_add= True)
    inst_status = models.CharField(max_length=20, blank=True, null=True, db_comment='Working\nNot Working\nReplaced\nRemoved\nLost')
    inst_active = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'instrument_biz'


class Remarks(models.Model):
    remarks_id = models.AutoField(primary_key=True)
    req_id = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=3, blank=True, null=True)
    response_json = models.JSONField(blank=True, null=True)
    response_dt = models.DateField(blank=True, null=True, auto_now_add= True)
    status = models.CharField(max_length=10, blank=True, null=True)
    remarks = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'remarks'

class IotRequest(models.Model):
    iot_id = models.AutoField(primary_key=True)
    biz = models.ForeignKey(BusinessInfo, models.DO_NOTHING, db_column='biz_id')
    req_id = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=3, blank=True, null=True)
    request_json = models.JSONField(blank=True, null=True)
    response_json = models.JSONField(blank=True, null=True)
    request_dt = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    response_dt = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    status = models.CharField(max_length=10, blank=True, null=True)
    remarks = models.IntegerField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'iot_request'


class LkrCatalog(models.Model):
    height = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    depth = models.IntegerField(blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    added_date = models.DateField(blank=True, null=True, auto_now_add= True)

    class Meta:
        # managed = False
        db_table = 'lkr_catalog'


class LkrStatusLog(models.Model):
    biz_lkr = models.ForeignKey(BizLkr, models.DO_NOTHING)
    status_cd = models.CharField(max_length=1)
    added_dt = models.DateTimeField(auto_now_add= True)

    class Meta:
        # managed = False
        db_table = 'lkr_status_log'


class LkrSummary(models.Model):
    biz = models.ForeignKey(BusinessInfo, models.DO_NOTHING, db_column='biz')
    lkr_type = models.ForeignKey(BizLkrType, models.DO_NOTHING)
    status_cd = models.CharField(max_length=1)
    status_count = models.IntegerField(db_column='status_count')  # Field renamed to remove unsuitable characters.
    updated_dt = models.DateTimeField(auto_now=True)
    location_id = models.IntegerField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'lkr_summary'


class LockStatusLog(models.Model):
    biz_lkr = models.ForeignKey(BizLkr, models.DO_NOTHING)
    status_cd = models.CharField(max_length=1, db_comment='Open(O) or Closed(C)\n')
    added_dt = models.DateTimeField(auto_now_add= True)

    class Meta:
        # managed = False
        db_table = 'lock_status_log'


class LockCmd(models.Model):
    lock_id = models.IntegerField(primary_key=True)
    biz_id = models.IntegerField()
    loc_id = models.IntegerField()
    cu_id = models.CharField(max_length=3)
    cu_lock_no = models.CharField(max_length=2)
    lock_no = models.CharField(max_length=3)
    open_cmd = models.CharField(max_length=20)
    status_cmd = models.CharField(max_length=20)
    class Meta:
        # managed = False
        db_table = 'lock_cmd'

class LockerStatus(models.Model):
    id = models.AutoField(primary_key=True)
    biz_id = models.IntegerField(null=True, default=None)
    loc_id = models.IntegerField(null=True, default=None)
    locker_id = models.IntegerField(null=True, default=None)
    lock_status = models.CharField(max_length=1, null=True, default=None)
    ir_status = models.CharField(max_length=1, null=True, default=None)
    added_dt = models.DateTimeField(null=True, default=None)
    class Meta:
        # managed = False
        db_table = 'locker_status'

class Payment(models.Model):
    payment_gateway = models.CharField(max_length=45, blank=True, null=True)
    payment_type = models.CharField(max_length=45, blank=True, null=True)
    ref_id = models.CharField(max_length=45, blank=True, null=True)
    ref_id_type = models.CharField(max_length=45, blank=True, null=True)
    biz_id = models.IntegerField(null=True, blank=True)
    extended_duration = models.DurationField(blank=True, null=True)
    loc_id = models.IntegerField(null=True, blank=True)
    book_id =models.IntegerField(blank=True, null=True)
    cust_id =models.IntegerField(blank=True, null=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    payment_status = models.CharField(max_length=1, blank=True, null=True, db_comment = 'Open(O) or Failed(F) or Paid(P) ')
    intent = models.CharField(max_length=45, blank=True, null=True)
    pay_req = models.JSONField(blank=True, null=True)
    pay_res = models.JSONField(blank=True, null=True)
    added_dt = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    updated_dt = models.DateTimeField(blank=True, null=True, auto_now= True)

    class Meta:
        # managed = False
        db_table = 'payment'


class PaymentType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'payment_type'


class Prebook(models.Model):
    cust = models.ForeignKey(Customer, models.DO_NOTHING)
    biz = models.ForeignKey(BusinessInfo, models.DO_NOTHING)
    lkr_type = models.ForeignKey(BizLkrType, models.DO_NOTHING)
    amount_init = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    book_dt = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    emp_id = models.IntegerField(blank=True, null=True)
    payment_status = models.CharField(max_length=1, blank=True, null=True, db_comment='Payment Completed or not, initial value will be set to N, once payment is comepleted, this will be updated to Y')
    pay_req_json = models.JSONField(blank=True, null=True)
    pay_res_json = models.JSONField(blank=True, null=True)
    update_dt = models.DateTimeField(blank=True, null=True, auto_now= True)
    booking_hrs = models.DurationField(blank=True, null=True)
    location_id = models.IntegerField(blank=True, null=True)
    reference_id =  models.CharField(max_length=20, blank=True, null=True)
    plink_id = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'prebook'


class Reqreslog(models.Model):
    req_res_id = models.AutoField(primary_key=True)
    req_res_biz = models.ForeignKey(BusinessInfo, models.DO_NOTHING)
    req_res_type = models.CharField(max_length=3, blank=True, null=True)
    req_res_json = models.JSONField(blank=True, null=True)
    req_res_added = models.DateTimeField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'reqreslog'


class RequestConfirm(models.Model):
    rc_id = models.AutoField(primary_key=True)
    book_h_hbook = models.ForeignKey(Book, models.DO_NOTHING)
    rc_status = models.CharField(max_length=1, blank=True, null=True, db_comment='request open\nmsg sent\nmsg delivered\nmsg read\nmsg confirm')

    class Meta:
        # managed = False
        db_table = 'request_confirm'

class RouterInfo(models.Model):
    id = models.IntegerField(primary_key=True)
    biz_id = models.IntegerField(null=True, default=None)
    loc_id = models.IntegerField(null=True, default=None)
    device_id = models.CharField(max_length=10, null=True, default=None)
    ip_range_start = models.CharField(max_length=15, null=True, default=None)
    ip_range_end = models.CharField(max_length=15, null=True, default=None)

    class Meta:
        # managed = False
        db_table = 'router_info'

class RouterStatus(models.Model):
    seq_no = models.AutoField(primary_key=True)
    biz_loc_id = models.CharField(max_length=10, null=True, default=None)
    router_ip = models.CharField(max_length=15, null=True, default=None)
    router_st = models.SmallIntegerField(null=True, default=None)
    added_dt = models.DateTimeField(null=True, default=None)

    class Meta:
        # managed = False
        db_table = 'router_status'
class SecurityPin(models.Model):
    sec_pin_id = models.AutoField(primary_key=True)
    sec_pin_pbook = models.ForeignKey(Prebook, models.DO_NOTHING)
    sec_pin_mobile_no = models.CharField(max_length=10, blank=True, null=True)
    sec_pin_pin = models.CharField(max_length=512, blank=True, null=True)
    sec_pin_added = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    attempt = models.IntegerField(default=0, blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'security_pin'

class BookToken(models.Model):
    token = models.CharField(max_length=160, blank=True, null=True)
    pbook = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    expired_at = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(default=0, blank=True, null=True, db_comment="false(0) alive, true(1) expired")
    class Meta:
        # managed = False
        db_table = 'book_token'

class Device(models.Model):
    id = models.IntegerField(primary_key=True)
    biz = models.ForeignKey(BusinessInfo, models.DO_NOTHING)
    name = models.CharField(max_length=45, blank=True, null=True)
    desc = models.CharField(max_length=200, blank=True, null=True)
    user_name = models.CharField(max_length=45, blank=True, null=True)
    added_dt = models.DateTimeField(blank=True, null=True, auto_now_add= True)
    class Meta:
        # managed = False
        db_table = 'device'