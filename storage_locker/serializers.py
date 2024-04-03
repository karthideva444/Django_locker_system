from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Activity,
    BizAccessType,
    BizLkr,
    BizLkrType,
    BizLocation,
    Book,
    BusinessInfo,
    CodeTable,
    CommTemplate,
    Customer,
    CustomerCommunication,
    Employee,
    InstrumentBiz,
    IotRequest,
    LkrCatalog,
    LkrStatusLog,
    LkrSummary,
    LockStatusLog,
    Payment,
    PaymentType,
    Prebook,
    Reqreslog,
    RequestConfirm,
    SecurityPin,
    Device,
)

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'

class BizAccessTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BizAccessType
        fields = '__all__'

class BizLkrSerializer(serializers.ModelSerializer):
    class Meta:
        model = BizLkr
        fields = '__all__'

class BizLkrTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BizLkrType
        fields = ['type_desc', 'amt_initial',
        'amt_per_unit','image_url','biz','processing_fee',
        'max_24_amt','min_hr','max_hr','increment_units','det_desc']

class BizLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BizLocation
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class BusinessInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessInfo
        fields = '__all__'

class CodeTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeTable
        fields = '__all__'

class CommTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommTemplate
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class CustomerCommunicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerCommunication
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class InstrumentBizSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstrumentBiz
        fields = '__all__'

class IotRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = IotRequest
        fields = '__all__'

class LkrCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LkrCatalog
        fields = '__all__'

class LkrStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LkrStatusLog
        fields = '__all__'

class LkrSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = LkrSummary
        fields = '__all__'

class LockStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LockStatusLog
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = '__all__'

class PrebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prebook
        fields = '__all__'

class ReqreslogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reqreslog
        fields = '__all__'

class RequestConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestConfirm
        fields = '__all__'

class SecurityPinSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityPin
        fields = '__all__'

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class UserEmployeeSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer()
    class Meta:
        model = User
        fields = '__all__'
