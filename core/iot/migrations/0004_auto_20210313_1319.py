# Generated by Django 3.1.7 on 2021-03-13 13:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('iot', '0003_auto_20210310_2034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='controllercomponenttype',
            name='created_by',
            field=models.ForeignKey(blank=True, help_text='The user that created the type. Global types have no owner.', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
