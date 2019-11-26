FROM ubuntu:latest
MAINTAINER Stefano Duo <duostefano93@gmail.com>
RUN apt-get update && apt-get install -y git python3.6 python3-pip
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN apt-get install rabbitmq-server
WORKDIR /STAR_DICES-stories
COPY . .
RUN python3 setup.py develop
ENV LANG C.UTF-8
EXPOSE 5000
CMD ["python3", "stories/app.py"]

