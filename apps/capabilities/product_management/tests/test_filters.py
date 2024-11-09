import pytest
from django.contrib.auth import get_user_model
from apps.capabilities.product_management.filters import ChallengeFilter
from apps.capabilities.product_management.models import Challenge, Product
from apps.capabilities.talent.models import Person

@pytest.mark.django_db
class TestChallengeFilter:
    @pytest.fixture
    def user(self):
        return get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com'
        )

    @pytest.fixture
    def product(self, user):
        person, _ = Person.objects.get_or_create(user=user)
        
        return Product.objects.create(
            name="Test Product",
            short_description="Test",
            visibility=Product.Visibility.GLOBAL,
            person=person
        )

    @pytest.fixture
    def challenges(self, product_with_person):
        challenges = []
        challenges.append(Challenge.objects.create(
            title="Test Challenge 1",
            description="Test description",
            short_description="Short description",
            product=product_with_person,
            status=Challenge.ChallengeStatus.DRAFT,
            priority=Challenge.ChallengePriority.HIGH,
            reward_type=Challenge.RewardType.LIQUID_POINTS
        ))
        challenges.append(Challenge.objects.create(
            title="Test Challenge 2",
            description="Test description",
            short_description="Short description",
            product=product_with_person,
            status=Challenge.ChallengeStatus.ACTIVE,
            priority=Challenge.ChallengePriority.MEDIUM,
            reward_type=Challenge.RewardType.NON_LIQUID_POINTS
        ))
        return challenges

    def test_challenge_filter_status(self, challenges):
        f = ChallengeFilter({'status': Challenge.ChallengeStatus.DRAFT})
        filtered = f.qs
        assert filtered.count() == 1
        assert filtered.first().status == Challenge.ChallengeStatus.DRAFT

    def test_challenge_filter_priority(self, challenges):
        f = ChallengeFilter({'priority': Challenge.ChallengePriority.HIGH})
        filtered = f.qs
        assert filtered.count() == 1
        assert filtered.first().priority == Challenge.ChallengePriority.HIGH

    def test_challenge_filter_reward_type(self, challenges):
        f = ChallengeFilter({'reward_type': Challenge.RewardType.LIQUID_POINTS})
        filtered = f.qs
        assert len(filtered) == 1
        assert filtered[0].reward_type == Challenge.RewardType.LIQUID_POINTS

    def test_challenge_filter_multiple_criteria(self, challenges):
        f = ChallengeFilter({
            'status': Challenge.ChallengeStatus.DRAFT,
            'priority': Challenge.ChallengePriority.HIGH,
            'reward_type': Challenge.RewardType.LIQUID_POINTS
        })
        filtered = f.qs
        assert len(filtered) == 1
        challenge = filtered.first()
        assert challenge.status == Challenge.ChallengeStatus.DRAFT
        assert challenge.priority == Challenge.ChallengePriority.HIGH
        assert challenge.reward_type == Challenge.RewardType.LIQUID_POINTS

    def test_challenge_filter_no_matches(self, challenges):
        f = ChallengeFilter({
            'status': Challenge.ChallengeStatus.DRAFT,
            'priority': Challenge.ChallengePriority.LOW
        })
        filtered = f.qs
        assert filtered.count() == 0