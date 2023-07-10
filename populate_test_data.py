import os
import sys
import time
import django
# from talent.models import Person

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openunited.settings")
django.setup()

print("Django version: " + django.get_version())


proceed = input("Running this script will replace all your current data. Ok? (Y/N)").lower()[0]

if proceed != "y":
    print("Stopped at your request")
else:

    sys.stdout.write("\r.....Deleting all data".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    # print(Person.object.all().count())

    sys.stdout.write("\r.....Create Person records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

    #Create Person records 

    # gary = Person(full_name='Gary Garner',email='test+garry@openunited.com')
    # gary.save()
    
    # shirly = Person(full_name='Shirley Ghostman',email='test+shirly@openunited.com')
    # shirly.save()

    sys.stdout.write("\r.....Create Profile records".ljust(80, "."))
    sys.stdout.flush()
    time.sleep(0.5)

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
    
   
