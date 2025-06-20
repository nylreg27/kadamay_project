# Generated by Django 4.2.23 on 2025-06-20 02:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('contribution_type', '0001_initial'),
        ('individual', '0001_initial'),
        ('church', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payment', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='payment',
            options={'ordering': ['-date_paid', '-or_number'], 'verbose_name': 'Payment', 'verbose_name_plural': 'Payments'},
        ),
        migrations.RemoveField(
            model_name='payment',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='deceased_member',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='is_legacy_record',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='payment_status',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='receipt_number',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='updated_by',
        ),
        migrations.AddField(
            model_name='payment',
            name='or_number',
            field=models.CharField(blank=True, help_text='Official Receipt number (auto-generated)', max_length=50, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='remarks',
            field=models.TextField(blank=True, help_text='Any additional remarks or notes', null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('Paid', 'Paid'), ('Pending', 'Pending'), ('Cancelled', 'Cancelled')], default='Pending', help_text='Current status of the payment', max_length=20),
        ),
        migrations.AlterField(
            model_name='coveredmember',
            name='amount_allocated',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Amount allocated to this covered member', max_digits=10),
        ),
        migrations.AlterField(
            model_name='coveredmember',
            name='individual',
            field=models.ForeignKey(help_text='The individual covered by this payment (payee)', on_delete=django.db.models.deletion.CASCADE, related_name='payments_covered', to='individual.individual'),
        ),
        migrations.AlterField(
            model_name='coveredmember',
            name='notes',
            field=models.TextField(blank=True, help_text="Notes specific to this covered member's allocation", null=True),
        ),
        migrations.AlterField(
            model_name='coveredmember',
            name='payment',
            field=models.ForeignKey(help_text='The payment that covers this member', on_delete=django.db.models.deletion.CASCADE, related_name='covered_members', to='payment.payment'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(decimal_places=2, help_text='Total amount of the payment', max_digits=10),
        ),
        migrations.AlterField(
            model_name='payment',
            name='cancellation_date',
            field=models.DateTimeField(blank=True, help_text='Date and time of payment cancellation', null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='cancellation_reason',
            field=models.TextField(blank=True, help_text='Reason for cancelling the payment', null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='church',
            field=models.ForeignKey(blank=True, help_text='The church associated with this payment', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='church.church'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='collected_by',
            field=models.ForeignKey(blank=True, help_text='User who collected the payment (e.g., Cashier, In-charge)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments_collected', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='payment',
            name='contribution_type',
            field=models.ForeignKey(blank=True, help_text='Type of contribution for this payment', null=True, on_delete=django.db.models.deletion.SET_NULL, to='contribution_type.contributiontype'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, help_text='Timestamp when the payment record was created'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='date_paid',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='Date and time the payment was made'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='gcash_reference_number',
            field=models.CharField(blank=True, help_text='GCash transaction reference number (if applicable)', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='individual',
            field=models.ForeignKey(blank=True, help_text='The individual who made this payment', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments_made', to='individual.individual'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='is_cancelled',
            field=models.BooleanField(default=False, help_text='Indicates if the payment has been cancelled'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payment_method',
            field=models.CharField(choices=[('Cash', 'Cash'), ('GCash', 'GCash')], help_text='Method of payment (Cash or GCash)', max_length=20),
        ),
        migrations.AlterField(
            model_name='payment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, help_text='Timestamp when the payment record was last updated'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='validated_by',
            field=models.ForeignKey(blank=True, help_text='User who validated the GCash payment', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments_validated', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='payment',
            name='validation_date',
            field=models.DateTimeField(blank=True, help_text='Date and time of GCash payment validation', null=True),
        ),
        migrations.DeleteModel(
            name='ContributionType',
        ),
    ]
