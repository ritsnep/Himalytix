# Generated by Django 5.0.14 on 2025-06-06 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usermanagement', '0013_permission_role_userrole'),
    ]

    operations = [
        migrations.AddField(
            model_name='userorganization',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
