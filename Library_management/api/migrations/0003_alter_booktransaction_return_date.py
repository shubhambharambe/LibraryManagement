# Generated by Django 5.1.4 on 2024-12-08 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_rename_booktransactions_booktransaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booktransaction',
            name='return_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]