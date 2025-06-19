# apps/individual/management/commands/generate_member_ids.py

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.individual.models import Individual # Import your Individual model

class Command(BaseCommand):
    help = 'Generates membership_ids for existing Individual records that do not have one.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to generate membership IDs for existing individuals...'))

        # Get all individuals that do NOT have a membership_id
        individuals_to_update = Individual.objects.filter(membership_id__isnull=True).order_by('pk')

        if not individuals_to_update.exists():
            self.stdout.write(self.style.SUCCESS('No individuals found without a membership ID. Exiting.'))
            return

        updated_count = 0
        
        # Iterate over each individual and generate an ID
        for individual in individuals_to_update:
            try:
                # Re-use the ID generation logic from the Individual model's save method
                # We'll temporarily set membership_id to None to force re-generation if needed,
                # though for isnull=True filter, it's already None.
                individual.membership_id = None # Ensure it's None to trigger generation logic
                individual.save() # Call save to trigger the custom save method
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'Successfully assigned ID {individual.membership_id} to {individual.full_name} (PK: {individual.pk})'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to assign ID to {individual.full_name} (PK: {individual.pk}): {e}'))

        self.stdout.write(self.style.SUCCESS(f'Finished! Updated {updated_count} individual(s) with new membership IDs.'))

