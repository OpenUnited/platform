from talent.models import Person, Skill, Expertise


class PersonService:
    @staticmethod
    def create(**kwargs):
        password = kwargs.pop("password", None)
        person = Person(**kwargs)
        if password:
            person.set_password(password)
        person.save()
        return person

    @staticmethod
    def get_by_id(id):
        person = Person.objects.get(id=id)
        return person

    @staticmethod
    def get_by_username(username: str) -> Person:
        return Person.objects.get(username=username)

    @staticmethod
    def update(person: Person, **kwargs):
        for key, value in kwargs.items():
            setattr(person, key, value)

        person.save()
        return person

    @staticmethod
    def delete(id):
        Person.objects.get(id=id).delete()

    @staticmethod
    def toggle_bounties(id):
        person = Person.objects.get(id=id)
        person.send_me_bounties = not person.send_me_bounties
        person.save()
        return person

    @staticmethod
    def make_test_user(id):
        person = Person.objects.get(id=id)
        person.is_test_user = True
        person.save()
        return person


class SkillService:
    @staticmethod
    def create(**kwargs):
        skill = Skill(**kwargs)
        skill.save()

        return skill


class ExpertiseService:
    @staticmethod
    def create(**kwargs):
        expertise = Expertise(**kwargs)
        expertise.save()

        return expertise
