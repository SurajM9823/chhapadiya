from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0003_order_orderitem'),
    ]

    operations = [
        migrations.AddField(model_name='sitesettings', name='bank_name', field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name='sitesettings', name='bank_account_name', field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name='sitesettings', name='bank_account_number', field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='sitesettings', name='bank_branch', field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name='order', name='payment_receipt', field=models.ImageField(blank=True, null=True, upload_to='receipts/')),
    ]
