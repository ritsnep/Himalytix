# Generated by Django 5.0.14 on 2025-06-04 18:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0003_alter_costcenter_organization'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='costcenter',
            unique_together=set(),
        ),
    ]
