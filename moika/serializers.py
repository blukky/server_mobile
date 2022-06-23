from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        exclude = ("user", )


class UserSerializer(serializers.ModelSerializer):
    location = LocationSerializer(many=False, read_only=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "email", "location")


class CarsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = ("id", 'body', "number")
