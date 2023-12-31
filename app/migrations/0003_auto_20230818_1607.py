# Generated by Django 2.2.28 on 2023-08-18 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20230818_1126'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('PUB', 'published'), ('EX', 'executed')], default='published', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='type',
            field=models.CharField(choices=[('BUY', 'buy'), ('SELL', 'sell')], default='sell', max_length=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='profile',
            name='btc_balance',
            field=models.FloatField(default=4.551695735119745),
        ),
    ]
