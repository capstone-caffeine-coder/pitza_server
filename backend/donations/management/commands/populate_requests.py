import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from donations.models import DonationRequest 

User = get_user_model()

fake = Faker('ko_KR')


class Command(BaseCommand):
    help = 'Populates the database with a specified number of fake donation requests.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--number',
            type=int,
            help='The number of donation requests to create.',
            default=70
        )

    def handle(self, *args, **options):
        number_of_requests = options['number']

        # Get existing users
        users = list(User.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR(
                "No users found in the database. Please create some users first "
                "(e.g., using 'manage.py createsuperuser' or a user population script)."
            ))
            return

        self.stdout.write(self.style.SUCCESS(f"Generating {number_of_requests} donation requests..."))

        created_count = 0
        for i in range(number_of_requests):
            requester = random.choice(users)
            name = fake.name()  # Name of the person needing donation
            age = random.randint(16, 70)
            sex = random.choice([choice[0] for choice in DonationRequest.SEX_CHOICES])
            blood_type = random.choice([choice[0] for choice in DonationRequest.BLOOD_TYPE_CHOICES])
            content = fake.paragraph(nb_sentences=5)
            location = fake.address()

            # Generate a due date between 1 day and 60 days from now
            donation_due_date = timezone.now().date() + timedelta(days=random.randint(1, 30))

            image_placeholder_path = f"../../../test_assets/test.png" 
            # e.g. 220923-0093
            donator_registered_id_value = fake.numerify(text='######-####')

            try:
                request = DonationRequest.objects.create(
                    requester=requester,
                    name=name,
                    age=age,
                    sex=sex,
                    blood_type=blood_type,
                    content=content,
                    image=image_placeholder_path,
                    location=location,
                    donation_due_date=donation_due_date,
                    donator_registered_id=donator_registered_id_value
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully created DonationRequest for '{request.name}' (ID: {request.id}) by {requester.nickname}"
                ))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error creating donation request for {name}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} donation requests."))