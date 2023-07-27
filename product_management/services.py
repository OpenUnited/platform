from .models import Challenge, Initiative, Capability, Tag, Product


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
