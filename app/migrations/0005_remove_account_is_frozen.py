from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_alter_account_bank_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='is_frozen',
        ),
    ]
