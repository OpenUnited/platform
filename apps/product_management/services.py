import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional, Tuple
from .models import Bounty, Challenge, Expertise
from . import forms

logger = logging.getLogger(__name__)

class ChallengeCreationService:
    def __init__(self, challenge_data: Dict, bounties_data: List[Dict], user):
        self.challenge_data = challenge_data
        self.bounties_data = bounties_data
        self.user = user
        self.logger = logging.getLogger(__name__)

    def validate_data(self) -> Optional[List[str]]:
        errors = []
        # Add validation logic
        return errors if errors else None

    def process_submission(self) -> Tuple[bool, Optional[str]]:
        try:
            if errors := self.validate_data():
                return False, str(errors)

            with transaction.atomic():
                challenge = self._create_challenge()
                if self.bounties_data:
                    self._create_bounties(challenge)
                self.logger.info(f"Challenge {challenge.id} created successfully")
                return True, None
        except Exception as e:
            self.logger.error(f"Error processing challenge submission: {e}")
            return False, str(e)

    def _create_challenge(self):
        return Challenge.objects.create(
            **self.challenge_data,
            created_by=self.user.person
        )

    def _create_bounties(self, challenge):
        for bounty_data in self.bounties_data:
            try:
                if isinstance(bounty_data, str):
                    import json
                    bounty_data = json.loads(bounty_data)
                
                bounty_data.pop('reward_type', None)  # Remove if exists since it's inherited
                
                # Create bounty directly
                bounty = Bounty.objects.create(
                    **bounty_data,
                    challenge=challenge,
                    status=Bounty.BountyStatus.AVAILABLE
                )
                
                # Handle expertise if provided
                if expertise_ids := bounty_data.get('expertise_ids'):
                    if isinstance(expertise_ids, str):
                        expertise_ids = expertise_ids.split(',')
                    bounty.expertise.add(*Expertise.objects.filter(id__in=expertise_ids))
                
            except Exception as e:
                logger.error(f"Error creating bounty: {e}")
                raise

class ProductService:
    @staticmethod
    def convert_youtube_link_to_embed(url: str):
        if url:
            return url.replace("watch?v=", "embed/")
