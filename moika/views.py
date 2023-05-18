import rest_framework.request
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth import authenticate
from rest_framework import status
from .models import *
from .serializers import *
from datetime import datetime
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
import random
import requests as r
import uuid
from yookassa import Configuration, Payment
import environ
from iqsms_rest import Gate

gate = Gate('z1682238630732', '453043')  # sms
env = environ.Env()

Configuration.account_id = env('ACCOUNT_ID')
Configuration.secret_key = env('SECRET_KEY')


def send_code(number):
    var_code, _ = VerifyCode.objects.get_or_create(phone=number)
    code = random.randint(999, 9999)
    if number == '+7(123) 456-7890':
        var_code.code = 2222
    else:
        var_code.code = code
        gate.send_message(number, f'Добро пожаловать в T4YС!\nКод авторизации: {code}', sender='T4YC')
        if float(gate.balance().split(';')[1]) <= 200.0:
            gate.send_message('+79260824036', f'T4YС\nБаланс СМС {gate.balance().split(";")[1]}', sender='T4YC')
    var_code.save()

def create_password():
    import string
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(16))
    return result_str


class apiLogin(APIView):
    def post(self, request):
        user = CustomUser.objects.filter(username=request.data.get('number')).first()
        if not user:
            user = CustomUser.objects.create_user(username=request.data.get('number'), password=create_password())
            send_code(number=user.username)
            return Response(status=200, data={"status": True})
        user.first_join = False
        user.save()
        send_code(number=user.username)
        return Response(status=200, data={"status": True})


class verifyCode(APIView):

    def post(self, request):
        ver_code = VerifyCode.objects.filter(phone=request.data.get("number")).first()
        if not ver_code:
            return Response(status=404,
                            data={"status": False, "detail": "На этот телефон не было отправлено сообщение"})
        if str(ver_code.code) != request.data.get('code'):
            return Response(status=400, data={"status": False, "detail": "Неверный код"})
        else:
            token = Token.objects.get(user=CustomUser.objects.get(username=request.data.get("number")))
            user = CustomUser.objects.get(username=request.data.get("number"))
            first_join = user.first_join
            user_serializers = UserSerializer(user).data
            return Response(status=200, data={"status": True, "token": token.key, "first_join": first_join,
                                              "user": user_serializers})


class userInfo(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.first_name = request.data.get("name")
        user.email = request.data.get("email")
        user.save()
        location, _ = Location.objects.get_or_create(user=user)
        location.location = request.data.get("location")
        location.save()
        return Response(data={"status": True}, status=200)


class supportEmail(APIView):
    permission_classes = [IsAuthenticated]

    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        mail = EmailMessage('Сообщение о проблемах', f'{request.POST.get("text")} \n\n Сообщение от {request.user.first_name} \n\n Телефон для обратной связи {request.user.username}', settings.EMAIL_HOST_USER, [settings.SUPPORT_EMAIL])
        if "file" in request.FILES.keys():
            file = request.FILES.get("file")
            mail.attach(file.name, file.read(), file.content_type)
        mail.send()
        return Response(status=200, data={"status": True})


class getCustomUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_ser = UserSerializer(request.user)
        return Response(status=200, data=user_ser.data)


class getCars(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cars = Car.objects.filter(user=request.user)
        cars_ser = CarsSerializer(cars, many=True)
        return Response(data=cars_ser.data)


class deleteCars(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        car = Car.objects.get(id=request.data.get("id"))
        car.delete()
        return Response(status=200, data={"status": True})


class editCar(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.data.get("id") is None:
            car = Car.objects.get(id=request.data.get("id"))
            car.number = request.data.get("number")
            car.body = request.data.get("body")
            car.save()
        else:
            Car.objects.create(user=request.user, number=request.data.get("number"), body=request.data.get("body"))
        return Response(status=200, data={"status": True})


class createOrder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Order.objects.create(user=request.user, order_id=int(request.data.get("id")))
        return Response(status=200, data={"id": request.data.get("id")})


class CreatePayment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Order.objects.count() + 1
        payment = Payment.create({
            "amount": {
                "value": request.data.get("price"),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"{env('TOPIC')}://payment?status=true"
            },
            "capture": False,
            "description": f"Заказ №{count}"
        }, uuid.uuid4())
        return Response(status=200, data={"uri": payment.confirmation.confirmation_url})


class CheckPayment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payment = Payment.find_one(request.data.get("uuid"))
        return Response(status=200, data={"status": True if payment.status == "waiting_for_capture" else False})


class AcceptPayment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        Payment.capture(request.data.get("uuid"))
        return Response(status=200, data={"status": True})


class CancelPayment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        idempotence_key = str(uuid.uuid4())
        response = Payment.cancel(
            request.data.get("uuid"),
            idempotence_key
        )
        return Response(status=200, data={"status": True})


class SetPushToken(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request: Request):
        push = PushToken.objects.filter(push_token=request.data.get("token")).first()
        if not push:
            if request.user:
                PushToken.objects.create(push_token=request.data.get("token"), user=request.user,
                                         ios_android=request.data.get("device"))
            else:
                PushToken.objects.create(push_token=request.data.get("token"),
                                         ios_android=request.data.get("device"))
        else:
            if request.user:
                push.user = request.user
                push.save()
        return Response(status=200, data={"push_token": request.data.get("push_token")})

    def delete(self, request: Request):
        push_token = PushToken.objects.filter(push_token=request.query_params.get("push_token")).first()
        if push_token:
            push_token.delete()
        return Response(status=200, data={"detail": True})


class GetPushToken(APIView):

    def get(self, request: Request):
        if "phone" in request.GET:
            push = PushToken.objects.filter(user__username=request.GET.get("phone"))
            if push:
                push_ser = PushTokenSerializers(push, many=True)
                return Response(status=200, data=push_ser.data)
            return Response(status=404, data={"detail": False})
        else:
            push_ser = PushTokenSerializers(PushToken.objects.all(), many=True)
            return Response(status=200, data=push_ser.data)
