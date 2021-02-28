from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("iot", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL("SELECT create_hypertable('iot_datapoint', 'time');"),
        # migrations.RunSQL(
        #     "ALTER TABLE farms_datapoint SET (timescaledb.compress, timescaledb.compress_segmentby = 'peripheral_component_id, data_point_type_id');"
        # ),
        # migrations.RunSQL(
        #     "SELECT add_compress_chunks_policy('farms_datapoint', INTERVAL '7 days');"
        # ),
    ]
