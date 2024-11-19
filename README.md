# THISuccess<sup>AI</sup>  Data Center

This repository contains a Flask application integrated with Dash to present data analytics, evaluation, and a test interface for the recommendation system hosted in our Productive Moodle System.

## Table of Contents

- [Project Purpose](#project-purpose)
- [Setup Instructions](#setup-instructions)
- [Prerequisites](#prerequisites)
- [Installation Locally](#installation-locally)
- [Installation in a server set up](#installation-in-a-server-set-up)
- [Components](#components)
- [License](#license)
- [Changelog](#changelog)

## Project Purpose

The purpose of that application is to create a real time dashboard that provide analytics and insights of the THISuccess<sup>AI</sup> Moodle platform. The application collects data automatically from various datasources and visualise them in an impactful way using a filtering system to support the user. One of the main goals is to get insights on KPIs, such as number of courses, users, Learning Nuggets as well as the usage of those activities. Additionally a specific page for analysing the interactions of our users with the chatbot is included. Finally the hosted recommendation system in our Moodle instance is also presented, explained and could be used to simulate learning paths and explain its workflow. This appplication should be able to become scallable and could be used with any moodle instance with some simple modifications. As most of the analysis parts are developed stand-alone they could easily turned on or off from the code.

## Setup Instructions

### Prerequisites

In order to install the application either locally or in a productive system it is required to have installed already:

- Python 3.10
- Docker
- Nginx
- Git
- Access to a Moodle System with or without an integrated Event Collection Service to fetch data
  
### Installation Locally

1. First, the app need to downloaded locally to a specified directory.

```bash
git clone https://github.com/ppagonis/Evaluation-Dashboard.git
cd /your/path/to/Evaluation-Dashboard
```

2. The `docker-compose.yml` file need to be set up in the correct directory:
`touch /you/path/to/Evaluation-Dashboard/docker-compose.yml`
And the below content need to be added there and be check from a yaml checker for its correctness:
`nano /your/path/to/Evaluation-Dashboard/docker-compose.yml`

```yaml
services:
  eval:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - github_access=${GITHUB_ACCESS}
        - username=ppagonis
    restart: always
    environment:
      - FLASK_APP=run.py
  nginx:
    image: nginx:1.23.1-alpine
    restart: always
    volumes:
      - ./conf/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    ports:
      - '80:80'

```

3. Additionally the nginx configuration needs to be done properly:

```bash
touch /your/path/to/Evaluation-Dashboard/conf/nginx.conf
nano /your/path/to/Evaluation-Dashboard/conf/nginx.conf
```

```conf
server {
    server_name localhost;
    
    rewrite_log on;
    keepalive_timeout   70;

    root /usr/share/nginx/html;
    location /eval {
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_pass_request_headers   on;
        proxy_pass http://eval:7005/;
    }
}
```

4. Create `crontab` file the automated tasks:

```bash
touch /your/path/to/Evaluation-Dashboard/crontab
nano /your/path/to/Evaluation-Dashboard/crontab
```

```bash
SHELL=/bin/bash
0-59/30 * * * * /app/cron.sh >> /app/cron.log 2>&1
# Don't remove the empty line at the end of this file. It is required to run the cron job

```

5. The ```Dockerfile``` needs to be also created:

```bash
touch /your/path/to/Evaluation-Dashboard/Dockerfile
nano /your/path/to/Evaluation-Dashboard/Dockerfile
```

```Dockerfile
FROM python:3.10

# Install packages
RUN apt-get update && apt-get -y install git cron libpq-dev supervisor

RUN mkdir app
WORKDIR /app
COPY requirements.txt requirements.txt
COPY ./cron.sh /app/cron.sh
COPY . .

# Upgrade pip and install requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn
ENV FLASK_APP=./run.py
  
# Add crontab file to the cron directory
COPY crontab /etc/cron.d/scheduler

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/scheduler
RUN chmod +x /app/cron.sh
  
# Apply the cron job
RUN crontab /etc/cron.d/scheduler

# Create the log file to be able to run tail
RUN touch /app/cron.log
RUN chmod 0644 /app/cron.log 

# Supervisor configuration file
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start supervisor
CMD ["/usr/bin/supervisord"]
```

6. Finally create the ```supervisord.conf``` to run simultaneously the Cron Job and the Application.

```bash
touch /your/path/to/Evaluation-Dashboard/Dockerfile
nano /your/path/to/Evaluation-Dashboard/Dockerfile
```

```conf
[supervisord]
nodaemon=true

[program:cron]
command=cron -f
stdout_logfile=/var/log/cron.log
stderr_logfile=/var/log/cron_err.log

[program:flask]
command=python -u run.py
directory=/app
autostart=true
autorestart=true
stdout_logfile=/var/log/flask.log
stderr_logfile=/var/log/flask_err.log
```

7. Start the docker and your maschine from the user interface and then start the application using the terminal.

```bash
cd /your/path/to/Evaluation-Dashboard
sudo docker compose build --no-cache && sudo docker compose up --build -d
```

8. Get inside the Docker Container either using the Docker GUI or Terminal and only for the first time run the ```cron.sh```.

```bash
sudo docker exec -it <CONTAINER-NAME> bash
./cron.sh
```

In case there are any error message try to rerun the command and it will be resolved.
9. Always the errors and the app logs could be observed there:

```bash
sudo docker exec -it <CONTAINER-NAME> bash
cat /var/log/flask_err.log
cat /var/log/flask.log
cat /app/cron.log
```

10. Finally the application should be accessible under the link ```http://localhost/eval/``` and it may take up to seven minutes to properly run (till that point you may encounter a Bad Gateway Error).

### Installation in a server set up

**The following set up information are referring only to an already existing server with a proper set up of Docker, Nginx and .env variables (such as GitHub Token).**
*Before starting the application in a productive server ensure the functionality locally as well as the data fetching from the Moodle System.*

1. Connect to your server
2. Move to the dedicated directory in which the whole set up is hosted `cd /path/to/your/directory`
3. Create the sub-directory for the application `mkdir eval`
4. Add the Dockerfile:

```bash
touch /eval/Dockerfile
nano /eval/Dockerfile
```

```Dockerfile
FROM python:3.10
ARG github_access
 # Install necessary packages
RUN apt-get update && apt-get -y install git cron libpq-dev supervisor
 # Clone the GitHub repository
RUN git clone --branch main https://$github_access:@github.com/ppagonis/Evaluation-Dashboard.git app
WORKDIR /app
 # Upgrade pip and install requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn
 # Add crontab file to the cron directory
ADD crontab /etc/cron.d/scheduler
 # Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/scheduler
RUN chmod +x /app/cron.sh
 # Apply the cron job
RUN crontab /etc/cron.d/scheduler
 # Create the log file to be able to run tail
RUN touch /app/cron.log
RUN chmod 0644 /app/cron.log
 # Supervisor configuration file
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
 # Start supervisor
CMD ["/usr/bin/supervisord"]
 ```

5. Add the `supervisord.conf`:

```bash
touch /eval/supervisord.conf
nano /eval/supervisord.conf
```

```conf
[supervisord]
nodaemon=true
[program:cron]
command=cron -f
stdout_logfile=/var/log/cron.log
stderr_logfile=/var/log/cron_err.log
[program:flask]
command=python -u run.py
directory=/app
autostart=true
autorestart=true
stdout_logfile=/var/log/flask.log
stderr_logfile=/var/log/flask_err.log
```

6. Add the `crontab`:

```bash
touch /eval/crontab
nano /eval/crontab
```

```bash
SHELL=/bin/bash
0-59/30 * * * * /app/cron.sh >> /app/cron.log 2>&1
 # Don't remove the empty line at the end of this file. It is required to run the cron job

 ```

7. Create and run the container
`sudo docker compose build --no-cache eval && sudo docker compose up --build -d eval`
8. Restart the nginx `sudo docker compose restart nginx`
9. After the container is up get inside the Docker Container in Terminal and only for the first time run the ```cron.sh```.

```bash
sudo docker exec -it <CONTAINER-NAME> bash
./cron.sh
```

In case there are any error message try to rerun the command and it will be resolved.

10. If you are using the Success<sup>AI</sup> server he app should now be running on [Success<sup>AI</sup> Data Center](https://success-ai.rz.fh-ingolstadt.de/eval/) otherwise it should run here `https://<YOUR-SERVER-IP-ADRESS>/eval/`. The application may take up to seven minutes to properly run (till that point you may encounter a Bad Gateway Error)
11. Always the errors and the app logs could be observed there:
```bash
sudo docker exec -it <CONTAINER-NAME> bash
cat /var/log/flask_err.log
cat /var/log/flask.log
cat /app/cron.log
```

## Components

### Data Fetcher

One of the main components in order the application to work is the Data Fetcher. Everything that has to do with the data collection are stored in the `./event_process` directory and in the `./dataset.py`. Those two places are the only ones that collects or process data.
*However this component is optional and any other data fetcher could work properly to visualise your own data. In the case the data are not coming from THISuccess<sup>AI</sup> official Moodle, then it is required to restructure the application in order to fit the variables.*

#### `./DataFetcher/events.py`

The above file is the main file that fetches, caches and merges the event collection data from Moodle and the metadata from the Learning Nuggets in Moodle.
In that file it is defined the url to fetch the data from the Event Collection Database and the url to fetch information of the Metadata. Those two are cached in two separate JSON objects to ensure faster processing of the data. The cache is expiring after 1 hour and then new data are to be fetched.
Then the data are prepared to be used in the Dash and Flask applications by changing data types, merging them or creating additional needed columns.

#### `./DataFetcher/chat_hist.py`

Similarly to the previous file, here the called data are only about the chatbot. All the data are called and cached for an hour and then they are preprocessed in order to be used from the Dash application.

#### `./DataFetcher/scheduled.py`

This script is intended to be used in a scheduled CRON job for automating event data processing tasks.
It uses the `EventHandling` class from the `events` module to handle data preprocessing, and saves the processed data to a CSV file (one for Events+Metadata and one fr Chatbot).

### Main Flask Application

The main host application is based on python's Flask as well as HTML and CSS to render pages. The application is organised using Blueprints and to ensure that the components are stand-alone parts, thus they could be easily be shown or hidden. In the `run.py` the data from the `./DataFetcher/scheduled.py`are called and using a threading mechanism they are realoding every three minutes to show some basic in information in the home page. Additionally the `__init__.py` sets up the recommendation system and also from there the user can "Activate" or "Deactivate" the respected dash applications. From the application as well the user can access and download the processed data from the Event Collection Service to perform individual analysis (user ids are hashed). Mostly Flask used for creating an all in one webpage including Dash Dashboards, Analytics, Recommendations and data downloder

### Usage Analytics Dashboard

The Usage Analytics Dashboard uses the collected data from the Event Collection Database and the Metadata to provide automated KPIs in the course usage, learning nugget usage as well as Learning Block usage. The application is completely written in Dash and facilitates the Pandas Dataframe usabilities using a lot of dynamic filters to the extract the desired information. The filter are not only time specific (Academic Year, Semester, Specific Time Frame) but also content specific (Course, Learning Block, Learning Nugget, Learning Nugget Type).
The Dash app automatically perfoms an internal cache in order to be able to fetch the newest data without problem using `diskcache`. The app is structured in way that the whole Dash app is a method and the return statement is the whole app. Inside that method the filters and the layout is created and it has to be mentioned that custom css are used to style the application. The Dash app is included in the individual routes as an iframe and it runs always as a stand-alone app in a separate routing. The returned graphics are always a bar chart that visualise the number of clicks per day per Learning Nugget / Learning Block / Learning Nugget Type / Difficulty level and an extractable table with those information. Additionally if a course is chosen it will provide a pie chart with the ration of Learning Nuggets used compared to the existing amount of Learning Nuggets.
Additional information for the code could be found in the docstring inside the file and in the comments in the app.

### Score Analytics Dashboard

**Currently under development**
The Score Analytics Dashboard will be used to perform automatic data analysis to the gathered score of the students and proper visualisation. Individual filters will create provide additional insights.
The Dash app is included in the individual routes as an iframe and it runs always as a stand-alone app in a separate routing.

### Chatbot Analytics Dashboard

The Chatbot Analytics Dashboard creates a new page that visualises information of the Productive Chatbot of THI's Moodle THIM. Currently there are three different views available that presents the usability, answering ratio as well number of messages exchanges per user.
The Dash app is included in the individual routes as an iframe and it runs always as a stand-alone app in a separate routing.

### Recommendation System Test Interface

TBD
  
## License

This project is licensed under the MIT License - see the LICENSE file for details.
  
## Changelog

See `CHANGELOG.md` for the list of changes.
