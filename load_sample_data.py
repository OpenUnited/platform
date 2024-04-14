import os
import datetime
import random
import django
from random import choice, sample, randint, getrandbits
from django.apps import apps
import json
from utility.utils import *


# Utility function to clear rows by model name
# Deletes all the existing records before populating sample data according to the dictionary
def clear_rows_by_model_name(model_names_mapping: dict) -> None:
    for model_name, app_name in model_names_mapping.items():
        model = apps.get_model(app_name, model_name)
        model.objects.all().delete()


def generate_random_future_date():
    today = datetime.date.today()
    one_month_later = today + datetime.timedelta(days=60)
    random_date = today + datetime.timedelta(
        days=random.randint(0, (one_month_later - today).days)
    )

    return random_date


def create_capabilities() -> list:
    fancy_out("Create product area records")
    get = lambda node_id: ProductArea.objects.get(pk=node_id)
    root_1 = ProductArea.add_root(
        name="Root product area  1",
        description="Root Description of Capability 1",
    )
    root_2 = ProductArea.add_root(
        name="Root product area  2",
        description="Root Description of product area  2",
    )
    node_root_2 = get(root_2.pk).add_child(
        name="Child of a Root product area  2",
        description="Child Description of product area  2",
    )
    get(node_root_2.pk).add_sibling(
        name="Sibling of Child of Root product area  1",
        description="Sibling Description of Child of Root product area  1",
    )
    get(node_root_2.pk).add_sibling(
        name="Sibling of Child of Root product area  2",
        description="Sibling Description of Child of Root product area  2",
    )
    get(node_root_2.pk).add_child(
        name="Sibling of Child of Root product area  3",
        description="Sibling Description of Child of Root product area  3",
    )
    node = get(root_1.pk).add_child(
        name="product area 2", description="Description of product area  2"
    )
    get(node.pk).add_sibling(
        name="product area 3", description="Description of product area  3"
    )
    get(node.pk).add_sibling(
        name="product area 4", description="Description of product area  4"
    )
    get(node.pk).add_child(
        name="product area 5", description="Description of product area 5"
    )
    get(node.pk).add_child(
        name="product area 6", description="Description of product area 6"
    )
    get(node.pk).add_child(
        name="product area 7", description="Description of product area 7"
    )

    return ProductArea.objects.all()


# Function to read data from a JSON file
def read_json_data(file_name: str, model_name: str = None) -> dict | list:
    if model_name:
        fancy_out(f"Create {model_name.title()} records")
    with open(file_name, "r") as json_file:
        return json.load(json_file)


# Generate sample data for various models and populate the database
def generate_sample_data():
    # Create Capability model instances
    capabilities = create_capabilities()

    # Create Tag model instances
    tag_data = read_json_data("utility/sample_data/tag.json", "tag")

    tags = []
    for tag in tag_data:
        tags.append(TagService.create(**tag))

    # Create User model instances
    user_data = read_json_data("utility/sample_data/user.json", "user")

    users = []
    for ud in user_data:
        users.append(UserService.create(**ud))

    # Create Person model instances
    person_data = read_json_data("utility/sample_data/person.json", "person")

    # Person model has a non-nullable OneToOneField to User model. Make sure the length of `user.json`
    # and `person.json` are the same. Otherwise, the script throws an error
    for index, pd in enumerate(person_data):
        pd["user"] = users[index]

    people = []
    for pd in person_data:
        people.append(PersonService.create(**pd))

    # Create Skill model instances
    skill_data = read_json_data("utility/sample_data/skill.json", "skill")

    skills = []
    for sk in skill_data:
        skills.append(SkillService.create(**sk))

    skill_ids = [skill.id for skill in skills]
    skill_name_queryset = Skill.objects.filter(
        id__in=skill_ids, active=True, selectable=True
    ).values_list("name", flat=True)

    # Create Expertise model instances
    expertise_data = read_json_data(
        "utility/sample_data/expertise.json", "expertise"
    )

    expertise = []
    for exp in expertise_data:
        expertise.append(ExpertiseService.create(**exp))

    expertise_ids = [exp.id for exp in expertise]
    expertise_name_queryset = Expertise.objects.filter(
        id__in=expertise_ids, selectable=True
    ).values_list("name", flat=True)

    # Create Product model instances
    product_data = read_json_data(
        "utility/sample_data/product.json", "product"
    )

    # note: allow organizations to own products
    # todo: check `capability_start`
    products = []
    for index, pd in enumerate(product_data):
        # only the first `len(product_data)` person can own products
        # the rest of people are contributors
        person = people[index]
        pd["content_object"] = person

        product = ProductService.create(**pd)
        products.append(product)

    # Create ProductRoleAssignment instances (part 1/2)
    for index in range(0, len(product_data)):
        role = 1

        if index > len(product_data) // 2:
            role = 2

        person = people[index]
        product = products[index]
        ProductRoleAssignment.objects.create(
            person=person, product=product, role=role
        )

    # Create Challenge model instances
    challenge_data = read_json_data(
        "utility/sample_data/challenge.json", "challenge"
    )
    challenges = []

    # Create Bounty model instances
    bounty_data = read_json_data("utility/sample_data/bounty.json", "bounty")
    bounties = []

    CHALLENGE_COUNT = 10
    BOUNTY_CLAIM_COUNT = 20
    for index, product in enumerate(products):
        step = index * CHALLENGE_COUNT
        temp_challenge_data = challenge_data[step : step + CHALLENGE_COUNT]
        for elem in temp_challenge_data:
            elem["product"] = product
            elem["created_by"] = product.content_object
            # elem["initiative"] = choice(initiatives)
            # elem["capability"] = choice(capabilities)
            # elem["updated_by"] = choice(people)
            elem["reviewer"] = product.content_object

        for cd in temp_challenge_data:
            challenge = Challenge.objects.create(**cd)
            challenge.tag.set(sample(tags, k=randint(1, 3)))
            challenges.append(challenge)

        temp_bounty_data = bounty_data[step : step + CHALLENGE_COUNT]
        for index, bd in enumerate(temp_bounty_data):
            # For now, each challenge has a single bounty
            challenge = challenges[step + index]
            bd["challenge"] = challenge
            bd["skill"] = choice(skills)

        for bd in temp_bounty_data:
            bounty = BountyService.create(**bd)
            bounty.expertise.set(sample(expertise, k=randint(1, 4)))
            bounties.append(bounty)

        # Create BountyClaim model instances
        bounty_claims = []
        for index in range(0, BOUNTY_CLAIM_COUNT):
            person = people[(index % len(people)) + len(products)]
            bounty = bounties[(index % 10) + step]

            kind = 3
            if index < 5:
                kind = 0  # CLAIM_TYPE_DONE
                bounty.status = 4  # done
                bounty.challenge.status = 4  # done
            elif index >= 5 and index < 10:
                kind = 1  # CLAIM_TYPE_ACTIVE
                bounty.status = 3  # claimed
                bounty.challenge.status = 3  # claimed
            elif index >= 10 and index < 15:
                kind = 2  # CLAIM_TYPE_FAILED
                bounty.status = 2  # available
                bounty.challenge.status = 2  # available
            else:
                kind = 3  # CLAIM_TYPE_IN_REVIEW
                bounty.status = 5  # in review
                bounty.challenge.status = 5  # in review

            bounty.save()
            bounty_claim_dict = {
                "person": person,
                "bounty": bounty,
                "expected_finish_date": generate_random_future_date(),
                "kind": kind,
            }

            bounty_claim = BountyClaimService.create(**bounty_claim_dict)
            bounty_claims.append(bounty_claim)

        # Create BountyDeliveryAttempt model instances
        bounty_delivery_attempt_data = read_json_data(
            "utility/sample_data/bounty_delivery_attempt.json",
            "bounty_delivery_attempt",
        )
        completed_bounty_claims = [bc for bc in bounty_claims if bc.kind == 1]

        for data, bounty_claim in zip(
            bounty_delivery_attempt_data, completed_bounty_claims
        ):
            data["bounty_claim"] = bounty_claim
            data["person"] = bounty_claim.person
            work = BountyDeliveryAttempt.objects.create(**data)

            # Work is approved
            if work.kind == 0:
                work.bounty_claim.kind = 1  # ACTIVE
                work.bounty_claim.bounty.status = 3  # CLAIMED
                work.bounty_claim.bounty.challenge.status = 3  # CLAIMED
                work.save()
            elif work.kind == 1:
                work.bounty_claim.kind = 0  # DONE
                work.bounty_claim.bounty.status = 4  # DONE
                work.bounty_claim.bounty.challenge.status = 4  # DONE
                work.save()
            elif work.kind == 2:
                work.bounty_claim.kind = 2  # DONE
                work.bounty_claim.bounty.status = 2  # available
                work.bounty_claim.bounty.challenge.status = 2  # available

            # Create contributors
            person = work.person
            product = work.bounty_claim.bounty.challenge.product
            ProductRoleAssignment.objects.create(
                person=person,
                product=product,
                role=0,
            )

    # Create Idea model instances
    idea_data = read_json_data("utility/sample_data/idea.json", "idea")

    index = 0
    for product in products:
        for i in range(index, index + 5):
            data = idea_data[i]
            data["product"] = product
            data["person"] = choice(people)
            Idea.objects.create(**data)

    # Create Bug model instances
    bug_data = read_json_data("utility/sample_data/bug.json", "bug")

    index = 0
    for product in products:
        for i in range(index, index + 5):
            data = bug_data[i]
            data["product"] = product
            data["person"] = choice(people)
            Bug.objects.create(**data)

    # Create Initiative model instances
    initiative_data = read_json_data(
        "utility/sample_data/initiative.json", "initiative"
    )

    index = 0
    for product in products:
        for i in range(index, index + 5):
            data = initiative_data[i]
            data["product"] = product
            Initiative.objects.create(**data)

    # Create PersonSkill model instances
    fancy_out(f"Create PersonSkill records")

    people = Person.objects.all()
    for person in people:
        bounty_claims = BountyClaim.objects.filter(person=person)

        if not bounty_claims:
            continue

        skill_ids = []
        expertise_ids = []
        for bc in bounty_claims:
            skill_ids.append(bc.bounty.skill.id)
            expertise_ids.extend([exp.id for exp in bc.bounty.expertise.all()])

        skill_name_queryset = Skill.objects.filter(
            id__in=set(skill_ids), active=True, selectable=True
        ).values_list("name", flat=True)

        expertise_name_queryset = Expertise.objects.filter(
            id__in=set(expertise_ids), selectable=True
        ).values_list("name", flat=True)

        PersonSkill.objects.create(
            person=person,
            skill=list(skill_name_queryset),
            expertise=list(expertise_name_queryset),
        )

    # Create Review model instances
    feedback_data = read_json_data(
        "utility/sample_data/feedback.json", "feedback"
    )

    index = 0
    for product in products:
        bounty_claims = BountyClaim.objects.filter(
            bounty__challenge__product=product, kind=0
        )

        for bounty_claim in bounty_claims:
            data = feedback_data[index]
            data["provider"] = product.content_object
            data["recipient"] = bounty_claim.person
            index += 1

            Feedback.objects.create(**data)

    # Create Organisation model instances
    organisation_data = read_json_data(
        "utility/sample_data/organisation.json", "organisation"
    )

    organisations = []
    for org_data in organisation_data:
        organisations.append(OrganisationService.create(**org_data))

    # Create OrganisationAccount model instances
    organisation_account_data = read_json_data(
        "utility/sample_data/organisation_account.json", "organisation account"
    )

    for index, oad in enumerate(organisation_account_data):
        oad["organisation"] = organisations[index]

    organisation_accounts = []
    for oad in organisation_account_data:
        organisation_accounts.append(OrganisationAccountService.create(**oad))

    # Create OrganisationAccountCredit model instances
    organisation_account_credit_data = read_json_data(
        "utility/sample_data/organisation_account_credit.json",
        "organisation account credit",
    )

    for index, oac in enumerate(organisation_account_credit_data):
        oac["organisation_account"] = organisation_accounts[index]

    organisation_account_credits = []
    for oacd in organisation_account_credit_data:
        organisation_account_credits.append(
            OrganisationAccountCreditService.create(**oacd)
        )

    # Create PointPriceConfiguration instance
    fancy_out("Create a PointPriceConfiguration record")

    point_price_conf_service = PointPriceConfigurationService()
    point_price_conf_service.create(
        applicable_from_date=datetime.date.today(),
        usd_point_inbound_price_in_cents=2,
        eur_point_inbound_price_in_cents=2,
        gbp_point_inbound_price_in_cents=2,
        usd_point_outbound_price_in_cents=1,
        eur_point_outbound_price_in_cents=1,
        gbp_point_outbound_price_in_cents=1,
    )

    # Create Cart model instances
    cart_data = read_json_data("utility/sample_data/cart.json", "cart")

    for index, cd in enumerate(cart_data):
        cd["creator"] = choice(people)
        cd["organisation_account"] = organisation_accounts[index]

    carts = []
    for cd in cart_data:
        carts.append(CartService.create(**cd))

    fancy_out("Complete!")


def run_data_generation():
    # proceed = input(
    #     "Running this script will replace all your current data. Ok? (Y/N)"
    # ).lower()

    # if not proceed or proceed[0] != "y":
    #     fancy_out("Execution Abandoned")
    #     exit()

    model_app_mapping = read_json_data(
        "utility/sample_data/model_app_mapping.json"
    )

    clear_rows_by_model_name(model_app_mapping)
    generate_sample_data()


if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE")
    )
    django.setup()

    from security.models import ProductRoleAssignment
    from talent.models import (
        Skill,
        Expertise,
        BountyDeliveryAttempt,
        BountyClaim,
        Person,
        PersonSkill,
        Feedback,
    )
    from product_management.models import (
        Bounty,
        Challenge,
        Idea,
        Bug,
        Initiative,
        ProductArea,
    )
    from commerce.services import (
        OrganisationService,
        OrganisationAccountService,
        OrganisationAccountCreditService,
        CartService,
        PointPriceConfigurationService,
    )
    from security.services import ProductRoleAssignmentService, UserService
    from talent.services import (
        PersonService,
        SkillService,
        ExpertiseService,
        StatusService,
        PersonSkillService,
        BountyClaimService,
        FeedbackService,
    )
    from product_management.services import (
        InitiativeService,
        TagService,
        ProductService,
        ChallengeService,
        BountyService,
        IdeaService,
        BugService,
    )

    run_data_generation()
