from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.account.models import Profile

class Command(BaseCommand):
    help = 'Creates Profile for Users missing one'

    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        for user in users:
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)
                self.stdout.write(f'Created profile for user: {user.username}')
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f'Total profiles created: {created_count}'))
