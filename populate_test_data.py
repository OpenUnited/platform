import os
import sys
import time
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openunited.settings")
django.setup()

from talent.models import Person, Skill, Expertise, PersonSkill
from security.models import User

print("Django version: " + django.get_version())

def update_stdout(message):
    output = ("\r....."+message).ljust(80, ".")
    sys.stdout.write(output)
    sys.stdout.flush()
    time.sleep(0.5)

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

    update_stdout("Create User & Person records")

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

    update_stdout("Setup Skills & Expertise records")

    load_reference_data("skill")
    load_reference_data("expertise")

    update_stdout("Create PersonSkill records")

    #Skill: Full-stack Development
    full_stack_development = Skill.objects.get(pk=106)

    #Expertise: Django
    django_expertise = Expertise.objects.get(pk=33)

    gary_skill = PersonSkill(person=gary, skill=full_stack_development.ancestry(), expertise=django_expertise.ancestry())
    gary_skill.save()

    update_stdout("Create User records")


    update_stdout("Create Product records")


    update_stdout("Create ProductPerson records")


    update_stdout("Create Capability records")


    update_stdout("Create Challenge records")


    update_stdout("Create Challenge Dependency records")


    update_stdout("Create Bounty records")


    update_stdout("Create BountyClaim records")


    update_stdout("Create BountyClaim Submission Attempt records")


    update_stdout("Create Portfolio records")

    
    update_stdout("Complete!")

