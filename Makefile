MANAGE = python manage.py

help:
	@echo "help               -- Print this help showing all commands.         "                     
	@echo "run                -- run the django development server             "
	@echo "test               -- run all tests                                 "
	@echo "migrate            -- prepare migrations and migrate                "
	@echo "admin              -- Created superuser and it prompt for password  "
	@echo "seed               -- Seed or load data from each app		 	   "
	@echo "setup              -- load all the data from the fixture to the app "
	@echo "dumpdata           -- Backup the data from the running django app   "
	@echo "tailwindcss        -- Generate Tailwindcss 						   "
	

rmpyc:
	find . | grep -E "__pycache__|\.pyc|\.pyo" | xargs sudo rm -rf

run:
	$(MANAGE) runserver

migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

seed:
	${MANAGE} loaddata canopy commerce engagement product_management security talent

setup:
	python reset_database.py 
	make migrate
	${MANAGE} loaddata canopy commerce engagement product_management security talent
	make test
dumpdata:
	${MANAGE} dumpdata canopy --output canopy/fixtures/canopy.json
	${MANAGE} dumpdata commerce --output commerce/fixtures/commerce.json
	${MANAGE} dumpdata engagement --output engagement/fixtures/engagement.json
	${MANAGE} dumpdata product_management --output product_management/fixtures/product_management.json
	${MANAGE} dumpdata security --output security/fixtures/security.json
	${MANAGE} dumpdata talent --output talent/fixtures/talent.json
	make format_fixtures

admin:
	$(MANAGE) createsuperuser --username=admin --email=admin@gmail.com
	
test:
	$(MANAGE) test

tailwindcss:
	tailwindcss -o ./static/styles/tailwind.css --minify

format_fixtures:
	jsonformat 	canopy/fixtures/canopy.json 
	jsonformat	commerce/fixtures/commerce.json 
	jsonformat	engagement/fixtures/engagement.json 
	jsonformat	product_management/fixtures/product_management.json 
	jsonformat	security/fixtures/security.json 
	jsonformat	talent/fixtures/talent.json
