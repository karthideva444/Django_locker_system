#!/usr/bin/env bash
GIT_TYPE=$1
RED='\033[0;31m'
LIGHT_ORANGE='\033[1;33m'
NC='\033[0m' # No Color

sed -i 's/80:80/8000:80/g' docker-compose.yml

sudo docker-compose stop
sudo docker-compose build
sudo docker-compose up -d
sudo docker ps

echo "Do you wish to purne the docker system?"
echo ${RED}WARNING! You are trying to remove:${NC}
echo 	${RED}- all stopped containers${NC}
echo	${RED}- all volumes not used by at least one container${NC}
echo	${RED}- all networks not used by at least one container${NC}
echo	${RED}- all dangling images${NC}

while true; do
    read -p "Do you wish to continue the above operation?" yn
    case $yn in
        [Yy]* ) sudo docker system prune -f; break;;
        [Nn]* ) echo "${LIGHT_ORANGE}Okay. Clean your docker system later if not, it can reduce your disk space in the long run.${NC}"; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
