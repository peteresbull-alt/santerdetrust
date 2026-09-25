from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_remove_account_is_frozen'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='account',
            name='is_closed',
        ),
    ]
