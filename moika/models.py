from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


# Create your models here.


class CustomUser(AbstractUser):
    first_join = models.BooleanField(default=True, verbose_name="Первый вход")
    username = models.CharField(max_length=255, verbose_name="Телефон", unique=True)



class PushToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    push_token = models.CharField(max_length=255, verbose_name="Хеш для отправки уведомлений", null=True, blank=True)

    class Meta:
        verbose_name = "Токен уведомления"
        verbose_name_plural = "Токены уведомлений"

    def __str__(self):
        return self.push_token


class VerifyCode(models.Model):
    phone = models.CharField(max_length=16, verbose_name="Номер телефона")
    code = models.IntegerField(verbose_name="Код", null=True, blank=True)

    class Meta:
        verbose_name = "Код верификации"
        verbose_name_plural = "Коды верификации"

    def __str__(self):
        return f"Код верификации {self.phone}"


class Location(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="location")
    location = models.CharField(max_length=255, verbose_name="Местоположение", null=True, blank=True)

    class Meta:
        verbose_name = "Местоположение"
        verbose_name_plural = "Местоположения"

    def __str__(self):
        return f"Местоположение пользователя {self.user.username}"


class Card(models.Model):
    number = models.CharField(verbose_name="Номер карты", max_length=20)
    require = models.CharField(max_length=255, verbose_name="Держатель карты")
    date_end = models.DateField(verbose_name="Дата конца карты")
    cvv = models.CharField(max_length=10, verbose_name="CVV")

    class Meta:
        verbose_name = "Карта"
        verbose_name_plural = "Карты"

    def __str__(self):
        return f"Карта {self.number}"


class CardList(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cards = models.ManyToManyField(Card, verbose_name="Список карт")

    class Meta:
        verbose_name = "Список карт"
        verbose_name_plural = "Списки карт"

    def __str__(self):
        return f"Список карт {self.user.username}"


# class Orders(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     order = models.Inte


class Car(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    body = models.CharField(max_length=255, verbose_name="Кузов")
    number = models.CharField(max_length=20, verbose_name="Номер машины")

    class Meta:
        verbose_name = "Машина"
        verbose_name_plural = "Машины"

    def __str__(self):
        return f"Машина {self.user.username}  с номером {self.number}"


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Пользователь")
    order_id = models.IntegerField(verbose_name="Идентификатор заказа")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ {self.user.username}  номер {self.order_id}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
