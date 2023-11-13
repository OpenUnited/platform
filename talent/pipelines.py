from .models import Person, Status


def create_person(
    strategy,
    backend,
    uid,
    response,
    details,
    user=None,
    social=None,
    *args,
    **kwargs,
):
    person_exists = Person.objects.filter(user=user).exists()
    if person_exists:
        return

    full_name = details.get("fullname")
    username = details.get("username")
    first_name = details.get("first_name")
    last_name = details.get("last_name")
    if full_name == "":
        full_name = f"{first_name} {last_name}"

    if full_name == "":
        full_name = username
        preferred_name = username
    else:
        if first_name == "":
            full_name = username
            preferred_name = username

    person = Person.objects.create(
        user=user,
        full_name=full_name,
        preferred_name=preferred_name,
    )

    Status.objects.create(person=person)
