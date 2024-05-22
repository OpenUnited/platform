import pytest
from model_bakery import baker


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    print("Enable database access for all tests")


@pytest.fixture
def skills():
    _skills = baker.make("talent.Skill", _quantity=10)
    for _skill in _skills:
        baker.make("talent.Expertise", skill=_skill)
    return _skills


@pytest.fixture
def skill():
    _skill = baker.make("talent.Skill")
    baker.make("talent.Expertise", skill=_skill)
    return _skill


@pytest.fixture
def expertise_list(skill):
    return baker.make(
        "talent.Expertise", skill=skill, _quantity=10, _fill_optional=True
    )


@pytest.fixture
def expertise(skill):
    return baker.make("talent.Expertise", skill=skill, _fill_optional=True)


@pytest.fixture
def bounty_claims(bounty, user):
    return baker.make(
        "talent.BountyClaim", bounty=bounty, person=user, _quantity=10
    )


@pytest.fixture
def bounty_claim(bounty, user):
    return baker.make("talent.BountyClaim", bounty=bounty, person=user)


@pytest.fixture
def feedback(users):
    return baker.make(
        "talent.BountyClaim", recipient=users[0], provider=users[0]
    )


@pytest.fixture
def Person_skills(user, skill, expertise_list):
    _person_skills = baker.make(
        "talent.PersonSkill",
        skill=skill,
        provider=user.person,
        _quantity=10,
    )
    for _person_skill in _person_skills:
        _person_skill.expertise.set([expertise_list])

    return _person_skills


@pytest.fixture
def Person_skill(user, skill, expertise_list):
    _person_skill = baker.make(
        "talent.PersonSkill", skill=skill, provider=user.person
    )
    _person_skill.expertise.add(expertise_list)
    return _person_skill
