# Generated by Django 4.2.23 on 2025-06-24 16:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('church', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('CASHIER', 'Cashier'), ('IN_CHARGE', 'In-Charge'), ('USER', 'User')], default='USER', max_length=20)),
                ('theme', models.CharField(choices=[('light', 'Light (Default DaisyUI)'), ('dark', 'Dark'), ('corporate', 'Corporate'), ('retro', 'Retro'), ('cyberpunk', 'Cyberpunk'), ('valentine', 'Valentine'), ('halloween', 'Halloween'), ('forest', 'Forest'), ('aqua', 'Aqua'), ('luxury', 'Luxury'), ('dracula', 'Dracula'), ('cmyk', 'CMYK'), ('autumn', 'Autumn'), ('business', 'Business'), ('acid', 'Acid'), ('lemonade', 'Lemonade'), ('night', 'Night'), ('coffee', 'Coffee'), ('winter', 'Winter'), ('dim', 'Dim'), ('nord', 'Nord'), ('sunset', 'Sunset')], default='corporate', max_length=50)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pics/')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserChurch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('church', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_users', to='church.church')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_church', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Church Assignment',
                'verbose_name_plural': 'User Church Assignments',
                'unique_together': {('user', 'church')},
            },
        ),
    ]
