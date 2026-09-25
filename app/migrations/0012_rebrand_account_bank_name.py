from django.db import migrations, models


def rename_bank(apps, schema_editor):
    Account = apps.get_model('app', 'Account')
    Account.objects.filter(bank_name='Liberty Trust Equity').update(bank_name='Santerde Trust')


def revert_bank(apps, schema_editor):
    Account = apps.get_model('app', 'Account')
    Account.objects.filter(bank_name='Santerde Trust').update(bank_name='Liberty Trust Equity')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_remove_transaction_balance_after_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='bank_name',
            field=models.CharField(default='Santerde Trust', max_length=200),
        ),
        migrations.RunPython(rename_bank, revert_bank),
    ]
