from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(VerifyCode)
admin.site.register(Card)
admin.site.register(Car)
admin.site.register(CardList)
admin.site.register(Location)
admin.site.register(CustomUser)