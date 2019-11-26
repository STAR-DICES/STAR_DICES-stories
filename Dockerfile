FROM ubuntu:latest
MAINTAINER Stefano Duo <duostefano93@gmail.com>
RUN apt-get update
RUN apt-get install -y git python3.6 python3-pip
RUN git clone -q https://github.com/STAR-DICES/STAR_DICES-stories.git
WORKDIR /STAR_DICES-stories
RUN pip3 install -r requirements.txt
RUN python3 setup.py develop
ENV LANG C.UTF-8
EXPOSE 5000
CMD ["python3", "stories/app.py"]
