lint:
	pylint automig

psql:
	docker exec -it ${NAME} psql -U postgres

backend:
	# bring up local backend
	docker run --name ${NAME} -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} -d postgres:11
