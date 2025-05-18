import random
from faker import Faker
from django.core.management.base import BaseCommand
from login.models import User #

fake = Faker('ko_KR')


class Command(BaseCommand):
    help = 'Populates the database with a specified number of fake users (50-100 if no number given)'

    def add_arguments(self, parser):
        parser.add_argument('--number', type=int, help='The number of users to create.', default=random.randint(50, 100))

    def handle(self, *args, **options):
        number_of_users = options['number']
        self.stdout.write(self.style.SUCCESS(f"Generating {number_of_users} users..."))

        for i in range(number_of_users):
            email = fake.unique.email()
            # Ensure kakao_id is unique; Faker's unique might need careful handling for large numbers
            # or you might need a loop to ensure uniqueness if collisions are likely.
            kakao_id = None
            while kakao_id is None or User.objects.filter(kakao_id=kakao_id).exists():
                kakao_id = str(fake.random_number(digits=10, fix_len=True))

            nickname = fake.user_name()
            birthdate = fake.date_of_birth(minimum_age=18, maximum_age=65)
            sex = random.choice(['M', 'F'])
            blood_types = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
            blood_type = random.choice(blood_types)
            profile_picture = fake.image_url()

            try:
                # Prioritize using your CustomUserManager's create_user method
                if hasattr(User.objects, 'create_user'):
                    user = User.objects.create_user(
                        email=email,
                        password='testpassword123', # A default password
                        kakao_id=kakao_id,
                        nickname=nickname,
                        birthdate=birthdate,
                        sex=sex,
                        blood_type=blood_type,
                        profile_picture=profile_picture
                        # Set is_staff, is_superuser if needed, e.g.
                        # is_staff=fake.boolean(chance_of_getting_true=10)
                    )
                else: # Fallback if create_user isn't the standard one or not available
                    user = User(
                        email=email,
                        kakao_id=kakao_id,
                        nickname=nickname,
                        birthdate=birthdate,
                        sex=sex,
                        blood_type=blood_type,
                        profile_picture=profile_picture
                    )
                    user.set_password('testpassword123')
                    user.save()

                self.stdout.write(self.style.SUCCESS(f"Successfully created user {i+1}/{number_of_users}: {user.email}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error creating user {email}: {e}"))
                # If unique constraints are an issue, you might want to retry or log more carefully.

        self.stdout.write(self.style.SUCCESS("User population complete."))