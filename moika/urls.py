from .views import *
from django.urls import path


urlpatterns = [
    path('login', apiLogin.as_view()),
    path('set_code', verifyCode.as_view()),
    path('send_user_info', userInfo.as_view()),
    path('support', supportEmail.as_view()),
    path('get_user', getCustomUser.as_view()),
    path('get_cars', getCars.as_view()),
    path('delete_cars', deleteCars.as_view()),
    path("edit_car", editCar.as_view()),
    path("create_order", createOrder.as_view()),
    path("set_push_token", SetPushToken.as_view()),
    path("get_push_token", GetPushToken.as_view()),

]