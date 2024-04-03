# Build Images:
docker-compose build

# Start Containers:
docker-compose up

# If you want to run it in the background, you can use the -d option:
docker-compose up -d

# View Running Containers:
docker-compose ps

# Stop Containers:
docker-compose down

# use -v as well to remove volumes:
docker-compose down -v

# To run a specific docker-compose file
docker-compose -f docker-compose.dev.yml up

# To restart Nginx 
sudo service nginx restart 

# To enter into the running docker container 
sudo docker exec -it container name  /bin/bash
sudo docker exec -it storage_locker_backend_1 /bin/bash# Django_locker_system
