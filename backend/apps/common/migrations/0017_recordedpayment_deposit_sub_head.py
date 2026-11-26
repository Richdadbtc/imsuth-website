from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('common', '0016_recordedpayment_rf_breakdown')]
    operations = [migrations.AlterField(model_name='recordedpayment',name='sub_head',field=models.CharField(max_length=16,blank=True,default='',choices=[('overhead','Over-head'),('rf','R/F'),('drf','DRF'),('deposit','Deposit')]))]
