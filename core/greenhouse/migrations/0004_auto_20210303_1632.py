# Generated by Django 3.1.7 on 2021-03-03 16:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('iot', '0002_add_hypertable'),
        ('greenhouse', '0003_auto_20210228_0952'),
    ]

    operations = [
        migrations.AddField(
            model_name='trackingimage',
            name='site',
            field=models.ForeignKey(blank=True, help_text='If not attached to a hydroponic system, to which site it belongs.', null=True, on_delete=django.db.models.deletion.CASCADE, to='iot.site'),
        ),
        migrations.AlterField(
            model_name='trackingimage',
            name='hydroponic_system',
            field=models.ForeignKey(blank=True, help_text='The hydroponic system to which it is attached to.', null=True, on_delete=django.db.models.deletion.CASCADE, to='greenhouse.hydroponicsystemcomponent'),
        ),
        migrations.AlterField(
            model_name='watercyclecomponent',
            name='water_cycle',
            field=models.ForeignKey(blank=True, help_text='To which water cycle this site entity belongs to.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='water_cycle_component_set', to='greenhouse.watercycle'),
        ),
        migrations.AlterField(
            model_name='watersensor',
            name='sensor_type',
            field=models.CharField(choices=[('InvalidSensor', 'Invalid sensor'), ('Temperature', 'Temperature sensor'), ('PhMeter', 'pH meter'), ('EcMeter', 'EC meter'), ('TdsMeter', 'TDS meter'), ('TurbidityMeter', 'Turbidity meter'), ('WaterLevel', 'Water level')], help_text='The sensor type.', max_length=64),
        ),
    ]
