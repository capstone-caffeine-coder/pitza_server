import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from board.models import DonationPost

fake = Faker('ko_KR')
User = get_user_model()

class Command(BaseCommand):
    help = '지정한 개수만큼 헌혈증 기부글(DonationPost)을 더미 데이터로 생성합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--number',
            type=int,
            help='생성할 헌혈증 기부글 수 (기본값: 10)',
            default=10
        )

    def handle(self, *args, **options):
        number_of_posts = options['number']

        # DB에 존재하는 유저 목록 조회
        users = list(User.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR(
                "유저가 하나도 없습니다. 먼저 'createsuperuser' 또는 더미 유저를 생성해 주세요."
            ))
            return

        self.stdout.write(self.style.SUCCESS(f"{number_of_posts}개의 헌혈증 기부글을 생성합니다..."))

        blood_types = [bt[0] for bt in DonationPost.BLOOD_TYPES]
        genders = [g[0] for g in DonationPost.GENDER_CHOICES]
        regions = ["서울", "부산", "대구", "광주", "인천", "울산", "경기도", "강원도", "전라도", "충청도", "제주도"]

        created_count = 0

        for i in range(number_of_posts):
            try:
                donor = random.choice(users)
                donor_name = fake.name()
                post = DonationPost.objects.create(
                    donor=donor,
                    donor_name=donor_name,
                    blood_type=random.choice(blood_types),
                    age=random.randint(18, 65),
                    gender=random.choice(genders),
                    region=random.choice(regions),
                    introduction=fake.paragraph(nb_sentences=3),
                    image=None
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"[{created_count}] {donor_name}님의 기부글 생성 완료 (ID: {post.id})"
                    #f"[{created_count}] {donor.email}님의 기부글 생성 완료 (ID: {post.id})"
                ))
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f"기부글 생성 중 오류 발생: {e}"
                ))

        self.stdout.write(self.style.SUCCESS(f"총 {created_count}개의 기부글을 생성했습니다."))
