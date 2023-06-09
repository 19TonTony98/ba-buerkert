# pull official base image
FROM python:3.11

# setup environment variable
ENV DockerHOME=/home/app/webapp

# set work directory
RUN mkdir -p $DockerHOME

# where your code lives
WORKDIR $DockerHOME

# copy whole project to your docker home directory.
COPY . $DockerHOME