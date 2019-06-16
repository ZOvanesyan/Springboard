FROM python:3.5

WORKDIR /usr/src/app

RUN git clone https://github.com/pjreddie/darknet /usr/src/app

RUN { \
    cd /usr/src/app; \
    make; \
    wget -O /usr/src/app/yolov3.weights https://pjreddie.com/media/files/yolov3.weights; \
    mkdir /usr/src/app/Img; \
    mkdir /usr/src/app/video; \
}


ADD requirements.txt /usr/src/app/requirements.txt
ADD darknet.py /usr/src/app/darknet.py
#ADD Img /usr/src/app/Img

RUN pip install virtualenv
RUN virtualenv -p python3.5 virtual
RUN /usr/src/app/virtual/bin/pip3.5 install -r /usr/src/app/requirements.txt
#RUN /bin/bash -c "source /virtual/bin/activate"

CMD ["/usr/src/app/virtual/bin/python3.5", "/usr/src/app/darknet.py"]


