# platform

This is the Django-based platform that powers OpenUnited. Django apps are used to create separate domains:

- Product Management (Product, Capability, Initiative, Challenge, Bounty etc.)
- Talent (Person, Skill, BountyClaim etc.)
- Commerce (Organisation, Points & Payments etc.)
- Engagement (Notifications etc.)

Each app/domain has a services.py file that implements the services that comprise the interface use by other apps.

This repo contains the full platform including the frontend (which is "deliberately simple"*), however in the workflow we prototype and specify the target UX as code in the [UX Prototype repo](https://github.com/OpenUnited/ux-prototype)

Regarding the deliberately simple frontend, we use [Jinja](https://jinja.palletsprojects.com/en/3.1.x/) templates, [TailwindCSS](https://tailwindcss.com/), [TailwindUI](https://tailwindui.com/), plain javascript, and a sprinkle of [HTMX](https://htmx.org/).

## Getting started / how to run this app

Good if you fork this repo, then depending on your local environment, do something like the following with "OpenUnited" changed for your own GitHub username:

```
git clone git@github.com:OpenUnited/platform.git
cd platform
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

