tests: dockerUp sleep2 initTestDb coverage dockerDown

prod: prodUp sleep2 updateDB prodStop

initTestDb:
	python3 ./electricity_consumption/init_database.py

updateDB:
	python3 ./electricity_consumption/update_database.py

coverage:
	coverage run -m pytest
	coverage report -m
	coverage erase

prodUp:
	docker compose -f './docker-compose-prod.yml' --env-file ./.env.prod up -d

prodStop:
	docker compose -f './docker-compose-prod.yml' --env-file ./.env.prod stop

dockerUp:
	docker compose up -d

dockerDown:
	docker compose down

sleep2:
	sleep 2