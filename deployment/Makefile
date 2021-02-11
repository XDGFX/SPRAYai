build-main:
	docker build -t detectron2:v0 .

build-deploy:
	docker build -t detectron2-deploy:v0 -f deploy.Dockerfile .

run-deploy:
	docker run -it --gpus all --name detectron2-deploy detectron2-deploy:v0