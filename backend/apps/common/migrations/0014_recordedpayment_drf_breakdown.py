from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('common', '0013_recordedpayment_overhead_breakdown')]
    operations = [migrations.AddField(model_name='recordedpayment', name='drf_breakdown', field=models.JSONField(blank=True, default=dict))]
