from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('payments', '0004_payment_cash_receiver')]
    operations = [migrations.AlterField(
        model_name='payment', name='cash_receiver',
        field=models.CharField(max_length=301, blank=True),
    )]
