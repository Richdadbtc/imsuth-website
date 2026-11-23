from django.db import migrations,models

class Migration(migrations.Migration):
    dependencies=[('accounts','0004_user_page_access')]
    operations=[migrations.AddField(model_name='user',name=name,field=models.DateTimeField(blank=True,null=True)) for name in ('banned_at','deleted_at')]
