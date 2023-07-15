import os
import django
import json
from utility.utils import *

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openunited.settings")
django.setup()

from talent.models import Person, Skill, Expertise, PersonSkill
from security.models import User

def load_reference_data(classname):
    klass = eval(classname.capitalize())
    klass.objects.all().delete()
    file = os.path.abspath("utility/reference_data/"+classname+".json")
    with open(file) as json_file:
        data_set = json.load(json_file)
        for data in data_set:
            obj = klass(**data)
            obj.save()

proceed = input("Running this script will replace all your current data. Ok? (Y/N)").lower()[0]

if proceed != "y":
    print("Stopped at your request")
else:
    fancy_out("Create User & Person records")
    
    #Clear and create User and Person records
    Person.objects.all().delete()
    User.objects.all().delete()

    gary_user = User(email="test+gary@openunited.com", username="garyg")
    gary_user.save()
    gary = Person(user=gary_user, full_name='Gary Garner', preferred_name='Gary', headline='I am Gary', test_user=True)
    gary.save()

    shirley_user = User(email="test+shirley@openunited.com", username="shirleyaghost")
    shirley_user.save()
    shirley = Person(user=shirley_user, full_name='Shirley Ghostman', preferred_name='Shirl', headline='Shirley Ghostman here', test_user=True)
    shirley.save()

    fancy_out("Setup Skills & Expertise records")

    load_reference_data("skill")
    load_reference_data("expertise")

    fancy_out("Create PersonSkill records")

    #Skill: Full-stack Development
    full_stack_development = Skill.objects.get(pk=106)

    #Expertise: Django
    django_expertise = Expertise.objects.get(pk=33)

    gary_skill = PersonSkill(person=gary, skill=full_stack_development.ancestry(), expertise=django_expertise.ancestry())
    gary_skill.save()

    fancy_out("Create User records")


    fancy_out("Create Product records")


    fancy_out("Create ProductPerson records")


    fancy_out("Create Capability records")


    fancy_out("Create Challenge records")


    fancy_out("Create Challenge Dependency records")


    fancy_out("Create Bounty records")


    fancy_out("Create BountyClaim records")


    fancy_out("Create BountyClaim Submission Attempt records")


    fancy_out("Create Portfolio records")

    
    fancy_out("Complete!")

