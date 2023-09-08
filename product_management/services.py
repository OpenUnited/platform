from .models import Challenge, Initiative, Capability, Tag, Product, Bounty, Idea


class ChallengeService:
    @staticmethod
    def create(**kwargs):
        challenge = Challenge(**kwargs)
        challenge.save()

        return challenge


class InitiativeService:
    @staticmethod
    def create(**kwargs):
        initiative = Initiative(**kwargs)
        initiative.save()

        return initiative


class CapabilityService:
    @staticmethod
    def create(**kwargs):
        capability = Capability(**kwargs)
        capability.save()

        return capability


class TagService:
    @staticmethod
    def create(**kwargs):
        tag = Tag(**kwargs)
        tag.save()

        return tag


class ProductService:
    @staticmethod
    def create(**kwargs):
        product = Product(**kwargs)
        product.save()

        return product

    @staticmethod
    def convert_youtube_link_to_embed(url: str):
        if url:
            return url.replace("watch?v=", "embed/")


class BountyService:
    @staticmethod
    def create(**kwargs):
        bounty = Bounty(**kwargs)
        bounty.save()

        return bounty


class IdeaService:
    @staticmethod
    def create(**kwargs):
        idea = Idea(**kwargs)
        idea.save()

        return idea
