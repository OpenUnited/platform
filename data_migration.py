import os
import django
import json


person_uuid_id_mapping = {}
extra_data_dict = {}


def read_json_data(file_name: str, model_name: str = None) -> dict:
    if model_name:
        print(f"Migrate {model_name.title()} records")
    with open(file_name, "r") as json_file:
        return json.load(json_file)


def delete_model_instances(sequence: list, model_name: str = None) -> None:
    if model_name:
        print(f"Deleting {model_name.title()} records")
    for elem in sequence:
        elem.delete()


def create_from_json(path: str, model: object, model_name: str = None, *args) -> list:
    result = []
    extra_data = []
    data = read_json_data(path, model_name)

    for elem in data:
        d = {}
        for arg in args:
            d[arg] = elem.pop(arg, None)

        extra_data.append(d)
        result.append(model.objects.create(**elem))

    return result, extra_data


def create_person(
    users,
    user_removed_args,
    person_path,
    person_model,
    person_model_name,
    *args,
):
    global person_uuid_id_mapping
    people = []
    data = read_json_data(person_path, person_model_name)

    person_removed_args = []
    for elem in data:
        d = {}
        for arg in args:
            d[arg] = elem.pop(arg, None)

        person_removed_args.append(d)

        user_id = d.get("user_id")
        index = 0
        for i, user_args in enumerate(user_removed_args):
            if user_args.get("id") == user_id:
                index = i
                break

        elem["user_id"] = users[index].id
        elem["preferred_name"] = elem.pop("first_name")
        p = person_model.objects.create(**elem)
        people.append(p)

        person_uuid_id_mapping[d.get("id")] = p.id

    return people, person_removed_args


import ipdb


def migrate():
    list_container = {}

    # try:
    data = [
        {
            "file_path": "utility/export/json/black_listed_usernames.json",
            "model": BlacklistedUsernames,
            "model_name": "blacklistedusernames",
        },
        {
            "file_path": "utility/export/json/work_tag.json",
            "model": Tag,
            "model_name": "tag",
        },
        {
            "file_path": "utility/export/json/work_skill.json",
            "model": Skill,
            "model_name": "skill",
        },
        {
            "file_path": "utility/export/json/work_expertise.json",
            "model": Expertise,
            "model_name": "expertise",
        },
        {
            "file_path": "utility/export/json/capability.json",
            "model": Capability,
            "model_name": "capability",
            # There is only one record that has comments_start_id assigned
            # We are dropping that value and are assigning null to that field
            "arguments": ("comments_start_id",),
        },
        {
            "file_path": "utility/export/json/work_product.json",
            "model": Product,
            "model_name": "product",
            "arguments": ("owner_id",),
        },
        {
            "file_path": "utility/export/json/work_initiative.json",
            "model": Initiative,
            "model_name": "initiative",
        },
        {
            "file_path": "utility/export/json/users_user.json",
            "model": User,
            "model_name": "user",
            "arguments": (
                "id",
                "is_logged",
            ),
        },
    ]

    global extra_data_dict

    for row in data:
        arguments = row.get("arguments")
        if arguments is None:
            arguments = []
        model_name = row.get("model_name").lower()

        objects, extra_data = create_from_json(
            row.get("file_path"),
            row.get("model"),
            model_name,
            *arguments,
        )
        list_container[model_name] = objects
        extra_data_dict[model_name] = extra_data

    person_data = {
        "file_path": "utility/export/json/talent_person.json",
        "model": Person,
        "model_name": "person",
        "arguments": (
            "id",
            "user_id",
            "email_address",
            "github_username",
            "git_access_token",
            "slug",
            "test_user",
        ),
    }

    users = list_container.get(model_name)
    users_extra_data = extra_data_dict.get(model_name)

    model_name = person_data.get("model_name")
    people, people_extra_data = create_person(
        users,
        users_extra_data,
        person_data.get("file_path"),
        person_data.get("model"),
        model_name,
        *person_data.get("arguments"),
    )

    list_container[model_name] = people
    extra_data_dict[model_name] = people_extra_data

    ###########################################################

    product_role_assignment_list = []
    product_role_assignment_data = read_json_data(
        "utility/export/json/talent_productperson.json", "productroleassignment"
    )

    person_history = []
    for elem in product_role_assignment_data:
        right = elem.pop("right")
        person_uuid = elem.pop("person_id")

        if person_uuid in person_history:
            continue
        else:
            person_history.append(person_uuid)

        p_id = person_uuid_id_mapping.get(person_uuid)
        if right == 3:
            elem["role"] = right - 1
        else:
            elem["role"] = right

        elem["person_id"] = p_id
        product_role_assignment_list.append(
            ProductRoleAssignment.objects.create(**elem)
        )

    list_container["productroleassignment"] = product_role_assignment_list

    challenge_list = []
    challenge_data = read_json_data(
        "utility/export/json/work_challenge.json", "challenge"
    )

    for elem in challenge_data:
        reviewer_id = elem.pop("reviewer_id")
        created_by_id = elem.pop("created_by_id")
        updated_by_id = elem.pop("updated_by_id")

        elem.pop("comments_start_id")

        elem["reviewer_id"] = person_uuid_id_mapping.get(reviewer_id)
        elem["created_by_id"] = person_uuid_id_mapping.get(created_by_id)
        elem["updated_by_id"] = person_uuid_id_mapping.get(updated_by_id)

        challenge_list.append(Challenge.objects.create(**elem))

    list_container["challenge"] = challenge_list

    bounty_list = []
    bounty_data = read_json_data("utility/export/json/work_bounty.json", "bounty")

    for elem in bounty_data:
        bounty_list.append(Bounty.objects.create(**elem))

    product_challenge_list = []
    product_challenge_data = read_json_data(
        "utility/export/json/work_productchallenge.json", "productchallenge"
    )

    for elem in product_challenge_data:
        product_challenge_list.append(ProductChallenge.objects.create(**elem))

    bounty_claim_list = []
    bounty_claim_data = read_json_data(
        "utility/export/json/matching_bountyclaim.json", "bountyclaim"
    )

    for elem in bounty_claim_data:
        person_uuid = elem.pop("person_id")
        elem["person_id"] = person_uuid_id_mapping.get(person_uuid)

        bounty_claim_list.append(BountyClaim.objects.create(**elem))

    bounty_delivery_attempt_list = []
    bounty_delivery_attempt_data = read_json_data(
        "utility/export/json/matching_bountydeliveryattempt.json",
        "bountydeliveryattempt",
    )

    for elem in bounty_delivery_attempt_data:
        person_uuid = elem.pop("person_id")
        elem["person_id"] = person_uuid_id_mapping.get(person_uuid)

        bounty_delivery_attempt_list.append(
            BountyDeliveryAttempt.objects.create(**elem)
        )

    # finally:
    #     print("Delete all the created records")
    #     model_names = list_container.keys()
    #     for model_name in model_names:
    #         delete_model_instances(list_container.get(model_name))


if __name__ == "__main__":
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE")
    )
    django.setup()

    from security.models import BlacklistedUsernames, User, ProductRoleAssignment
    from product_management.models import (
        Tag,
        Product,
        Capability,
        Initiative,
        Product,
        Challenge,
        Bounty,
        ProductChallenge,
    )
    from talent.models import (
        Skill,
        Expertise,
        Person,
        BountyClaim,
        BountyDeliveryAttempt,
    )

    migrate()
