MONGODB_USER ?= admin
MONGODB_PASS ?= yellow

docker_build_app_arm64:
	docker build \
		-f repository/infra/python/Dockerfile \
		--platform linux/arm64 \
		-t beescout:latest-arm64 .

docker_build_db_arm64:
	docker build \
		-f repository/infra/mongodb/Dockerfile \
		--build-arg MONGODB_USER=$(MONGODB_USER) \
		--build-arg MONGODB_PASS=$(MONGODB_PASS) \
		--platform linux/arm64 \
		-t beescout:latest-db-arm64 .

docker_build_app_amd64:
	docker build \
		-f repository/infra/python/Dockerfile \
		--platform linux/amd64 \
		-t beescout:latest-amd64 .

docker_build_db_amd64:
	docker build \
		-f repository/infra/mongodb/Dockerfile \
		--build-arg MONGODB_USER=$(MONGODB_USER) \
		--build-arg MONGODB_PASS=$(MONGODB_PASS) \
		--platform linux/amd64 \
		-t beescout:latest-db-amd64 .

docker_compose_up:
	docker compose up --build -d  

docker_remove_dangling_images:
	docker image prune -f

docker_create_network:
	docker network inspect exa-net >/dev/null 2>&1 || docker network create exa-net

service_stop:
	docker compose down -v

service_start: docker_build_app_image \
	docker_build_db_image \
	docker_create_network \
	docker_compose_up \
	docker_remove_dangling_images

copy_env_file:
	cp app/.env.example app/.env
