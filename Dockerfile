# pull official base image
FROM python:3.11


# setup environment variable
ENV DockerHOME=/home/app/webapp

# set work directory
RUN mkdir -p $DockerHOME

# where your code lives
WORKDIR $DockerHOME

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
# copy whole project to your docker home directory.
COPY . $DockerHOME
COPY influxdb_collector /home/app/influxdb_collector
# run this command to install all dependencies
RUN pip install -r requirements.txt
# port where the Django app runs
EXPOSE 8000/tcp
# start server
CMD python manage.py makemigrations
CMD python manage.py migrate
