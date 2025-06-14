# Generated by Django 5.2.1 on 2025-05-12 16:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usermanagement', '0002_remove_customuser_company_customuser_auth_provider_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserOrganization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_owner', models.BooleanField(default=False)),
                ('role', models.CharField(default='member', max_length=50)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usermanagement.organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_organizations',
                'unique_together': {('user', 'organization')},
            },
        ),
    ]
