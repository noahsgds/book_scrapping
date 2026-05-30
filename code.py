-- Code terminal a lancé --
docker build -t noah.test .
docker image
docker rmi
docker run noah.test



-- YAML--
services:
  python-app:
    build: . #(" ." = dans tous les composants)
    volumes:  # création d'un pont entre le fichier local et le container. Dès que je modifie source le container à acces au fichier dans volumes
      - ./src:/app
    container_name: noah.test


-- Suite -
docker ps (ceux qui tourne)
docker stop noah.test
docker ps -a (même ceux qui ne tournent plus)

-- Mettre à jour --
docker compose up #et lancer facilement

-- Automatisation --
RUN crontab /etc/cron.d/ datapipeline-cron #commande de run 

--Rentrer dans le container--
python_test bash
ls 
whereis python3

