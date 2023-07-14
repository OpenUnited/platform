import os
import sys
import time
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openunited.settings")
django.setup()

from talent.models import Person, PersonProfile
from security.models import User

print("Django version: " + django.get_version())

proceed = input("Running this script will replace all your current data. Ok? (Y/N)").lower()[0]

if proceed != "y":
    print("Stopped at your request")
else:

    sys.stdout.write("\r.....Deleting all data".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    print(Person.objects.all().count())

    sys.stdout.write("\r.....Create User & Person records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

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

    sys.stdout.write("\r.....Create Profile records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    #Clear and create PersonProfile records
    
    PersonProfile.objects.all().delete()

    gary_profile = PersonProfile(person=gary, overview="Hi, I am Gary! This is my overview.")
    gary_profile.save()

    shirley_profile = PersonProfile(person=shirley, overview="Hi, I am Shirley! This is my brief overview.")
    shirley_profile.save()


    sys.stdout.write("\r.....Create PersonSkill records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    

    sys.stdout.write("\r.....Create User records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    sys.stdout.write("\r.....Create Product records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    sys.stdout.write("\r.....Create ProductPerson records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    sys.stdout.write("\r.....Create Capability records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    sys.stdout.write("\r.....Create Challenge records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    sys.stdout.write("\r.....Create Challenge Dependency records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    sys.stdout.write("\r.....Create Bounty records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    sys.stdout.write("\r.....Create BountyClaim records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    sys.stdout.write("\r.....Create BountyClaim Submission Attempt records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)


    sys.stdout.write("\r.....Create Portfolio records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    sys.stdout.write("\r.....Complete!".ljust(80, "."))
    