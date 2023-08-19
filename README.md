# platform

This is the platform that powers OpenUnited. [Apps](https://docs.djangoproject.com/en/4.2/ref/applications/) are used to create "bounded contexts":

- Product Management (Product, Capability, Initiative, Challenge, Bounty etc.)
- Talent (Person, Skill, BountyClaim etc.)
- Commerce (Organisation, Points & Payments etc.)
- Engagement (Notifications etc.)

Each app has a services.py file that implements the "public" services interface for that app/bounded context.

This repo contains the full platform including the frontend - which is "deliberately simple"*. We prototype and specify the target UX, as code, in the [UX Prototype repo](https://github.com/OpenUnited/ux-prototype). The UX Prototype repo is not for production use, we use it instead of using Figma.

\* Our "deliberately simple" frontend means that we use [Jinja](https://jinja.palletsprojects.com/en/3.1.x/) templates, [TailwindCSS](https://tailwindcss.com/), [TailwindUI](https://tailwindui.com/), plain javascript, and a sprinkle of [HTMX](https://htmx.org/). Earlier we had a separate ReactJS frontend and a GraphQL API layer, however [such fanciness](https://www.youtube.com/watch?v=Uo3cL4nrGOk) failed to deliver the expected value, whilst creating complexity/friction... therefore, we now have a deliberately simple frontend.

## Getting started / how to run the OpenUnited platform locally

### Database setup

Please ensure you have a PostgreSQL server running. If you haven't already, you can [download and install PostgreSQL](https://www.postgresql.org/download/) 

By default, the OpenUnited platform will look for a database named "ou_db" and use "postgres" as both the username and password. For development purposes, if you already have a postgres server running locally with this default username/password combination, the easiest thing is to just create a database named: ou_db. To override the database settings, you can copy .env.example to .env and set the values you want.

### Running the platform locally

Please fork this repo, then depending on your local environment, do something like the following with "OpenUnited" changed for your own GitHub username.

```
git clone git@github.com:OpenUnited/platform.git
cd platform
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
./setup.sh
python manage.py runserver
```

Then navigate to: [http://localhost:8000/](http://localhost:8000/) in your browser.

Not working? Please check [the Django docs](https://docs.djangoproject.com/en/4.2/intro/tutorial01/) and make sure you have [PostgreSQL installed](https://www.google.com/search?q=how+to+install+postgresql)

### Running the platform locally using docker

Make sure you have docker install on your machine.

```
cp .env.example .env
cp docker.env.example docker.env

# Change them as you need

docker compose --env-file docker.env up --build
```
Then navigate to: [http://localhost:8000/](http://localhost:8000/) in your browser.
