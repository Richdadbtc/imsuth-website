from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('common', '0015_add_main_cashpoints')]
    operations = [migrations.AddField(model_name='recordedpayment', name='rf_breakdown', field=models.JSONField(blank=True, default=dict))]
