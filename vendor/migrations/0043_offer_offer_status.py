# Generated by Django 3.1.6 on 2021-02-21 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0042_auto_20210220_0621'),
    ]

    operations = [
        migrations.AddField(
            model_name='offer',
            name='offer_status',
            field=models.CharField(blank=True, default='Valid', max_length=40),
        ),
    ]