FROM python:3.10

#ARG github_access

# Install necessary packages
RUN apt-get update && apt-get -y install git cron libpq-dev supervisor

# Clone the GitHub repository
#RUN git clone --branch main https://$github_access:@github.com/ppagonis/Evaluation-Dashboard.git app
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
