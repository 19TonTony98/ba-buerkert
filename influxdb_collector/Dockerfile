## pull official base image
#FROM python:3.11
#
## Set the working directory in the container
#WORKDIR /home/app/collector
#
## Copy the requirements file into the container
#COPY requirements.txt .
#
## Install the Python dependencies
#RUN pip install --no-cache-dir -r requirements.txt
#
## Copy the rest of the application code into the container
#COPY . .
#
## Define the command to run your application
#CMD ["python", "collector.py"]
# pull official base image
FROM python:3.11

# setup environment variable
ENV DockerHOME=/home/app/collector

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

CMD ["python", "collector.py"]