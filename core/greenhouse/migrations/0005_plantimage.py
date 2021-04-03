# Generated by Django 3.1.7 on 2021-03-29 16:52

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('greenhouse', '0004_auto_20210303_1632'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlantImage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('image', models.ImageField(help_text='The image of a plant.', upload_to='')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The datetime of creation.')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The datetime of the last update.')),
                ('plant', models.ForeignKey(help_text='The primary plant in the image.', on_delete=django.db.models.deletion.CASCADE, to='greenhouse.plantcomponent')),
            ],
        ),
    ]