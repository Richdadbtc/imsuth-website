from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('common', '0017_recordedpayment_deposit_sub_head'), ('payments', '0005_cash_receiver_full_name')]
    operations = [migrations.AddField(model_name='recordedpayment',name='deposit_receipt',field=models.ForeignKey(null=True,blank=True,on_delete=django.db.models.deletion.PROTECT,related_name='linked_deposit_payments',to='payments.receipt'))]
