from django.urls import path
from .views import (
    AvailLockerView,
    PreBookView,
    CallbackView,
    ConfirmationView,
    AvailLkrLoc,
    AvailLkrLocToken,
    OpenLockerView,
    BusinessLocationView,
 
)
from .lkr_detail_view import AvailLkrSummaryView, BookInfoView, GetAmount, bookingpage
from .customer import CheckCustomerView, CustomerAuth

urlpatterns = [
    path("availLkr/biz/<str:pk>/", AvailLockerView.as_view(), name="availLocker"),
    path("availLkrDetail/<str:pk>/",AvailLkrSummaryView.as_view(),name="availdetail",),
    path("checkcust/", CheckCustomerView.as_view(), name="checkcust"),
    path("prebook/", PreBookView.as_view(), name="prebook"),
    path("callback/", CallbackView.as_view(), name="callback"),
    path("confirm/<str:pk>/", ConfirmationView.as_view(), name="confirm"),
    path("availLkr/loc/<int:pk>/", AvailLkrLoc.as_view(), name="availLocation"),
    path("availLkr/biz/<str:pk>/<int:mn>/", AvailLkrLocToken.as_view(), name="availLocation"),
    path("openlocker/", OpenLockerView.as_view(), name="openlocker"),
    path('getbizid/', BusinessLocationView.as_view(), name='busiloc'),
    path('getamount/', GetAmount.as_view(), name='getamount'),
    path("book/<int:pk>/", BookInfoView.as_view(), name='bookinfo'),
    path("authcustomer/", CustomerAuth.as_view(), name='authcustomer'),
    path("bookingpage/<str:token>/", bookingpage, name="BookingPage")
]
