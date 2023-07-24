# Bachlorarbeit Anton Maier
## Entwicklung einer Datenbankmit Weboberfläche zur Speicherung und Auswertungeiner Hefeassimilierungsanlage

Diese Bachelorarbeit enthält alle nötigen Komponenten um eine Django Weboberfläche
mit InfluxDB Datenbank zu betreiben. Dazu befindet sich ein [Dockerfile](Dockerfile) und 
eine [docker-compose.yml](docker-compose.yml) zum starten der Docker Container im Projekt. 
Die einzelnen Komponeten können auch außerhalb von Docker Containern betrieben werden,
dazu müssen die Einstellungen in [buerkert/settings.py](buerkert/settings.py) entsprechend angepasst werden.

### Vorbereitung
Zum Betreiben der InfluxDB mit dem Datacollector zur Weboberfläche 
müssen mehrere Verzeichnisse erstellt werden:

Datenbank:

/home/db/ -> Für den persisten Speicher der Datenbank

Datacollector:

 /home/app/res/ -> Dort müssen die Daten aus [res](res) abgelegt werden. 
 Diese sind notwendig für die Kommunikation zwischen Datencollector und Weboberfläche
 
/home/app/influxdb_collector/ -> Dort müssen die Daten aus [influxdb_collector](influxdb_collector) abgelegt werden.

Diese Verzeichnisse müssen nur nach veränderung in den jeweiligen project Verzeichnissen aktualliesiert werden


Optional:

/home/app/webapp/ -> Dort kann das gesamte Projekt als git-repo abgelegt werden


Benötigte Programme:

Auf der Hostumgebung wird Docker und Docker Compose benötigt

### Starten
Zum starten des gesamt Projekts:

in das Projekt Verzischnis wechseln 

z.B $cd /home/app/webapp

dann $docker compose up

oder $docker compose up --build um Container neu bauen zu lassen

um die Weboberfläche einzel zu starten wird Python 3.11 mit den [requirements.txt](requirements.txt) benötigt

dann mit $python3.11 manage.py runserver 

starten

###  Beenden

$docker compose down

### InfluxDB Einstellungen

In der InfluxDB Oberfläche(ereichbar über port 8086) muss ein User mit AccesToken hinterlegt sein. 
Dieser Token muss in [buerkert/settings.py](buerkert/settings.py) unter DATABASES['influx']['token'] hinterlegt werden