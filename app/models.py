from django.db import models
from djongo.models.fields import ObjectIdField, Field
from django.contrib.auth.models import User
import random
from enum import Enum

class Profile(models.Model):
    _id = ObjectIdField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ips = models.Field(default=[])
    subprofiles = models.Field(default={})
    btc_balance = models.FloatField(default=random.uniform(1, 10))


class Order(models.Model):
    class Types(Enum):
        BUY = 'buy'
        SELL = 'sell'

    class Status(Enum):
        PUB = 'published'
        EX = 'executed'

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    quantity = models.FloatField()
    type = models.CharField(max_length=10)
    status = models.CharField(max_length=10)