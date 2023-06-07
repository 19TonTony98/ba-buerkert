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
# run this command to install all dependencies
RUN pip install -r requirements.txt
# port where the Django app runs
EXPOSE 8000/tcp
# start server
CMD python manage.py makemigrations
CMD python manage.py migrate

# Install dependencies
RUN apt-get update && apt-get install -y supervisor

# Copy the supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start supervisord when the container launches
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]