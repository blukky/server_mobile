from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
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
import random


# Create your views here.

def send_code(number):
    var_code, _ = VerifyCode.objects.get_or_create(phone=number)
    code = random.randint(999, 9999)
    var_code.code = 2222  # code
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
            return Response(status=200, data={"status": True, "token": token.key, "first_join": first_join})


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

    # parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        mail = EmailMessage("Сообщение о проблемах", request.POST.get(
            "text") + f"\n\n Сообщение от {request.user.first_name} \n\n Телефон для обратной связи {request.user.username}",
                            settings.EMAIL_HOST_USER, [settings.SUPPORT_EMAIL])
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
