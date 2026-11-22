from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('common', '0011_rename_shared_cash_points')]
    operations = [migrations.AddField(
        model_name='recordedpayment', name='sub_head',
        field=models.CharField(max_length=16, choices=[('overhead','Over-head'),('rf','R/F'),('drf','DRF')], blank=True, default=''),
    )]
