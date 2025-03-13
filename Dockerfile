FROM docker.io/amd64/fedora:39

WORKDIR /home/

RUN yum repolist && \
    yum install git python3-pip -y

RUN git clone https://github.com/redhat-performance/yoda/ && \
    cd yoda && \
    python3 -m venv venv && \
    source /home/yoda/venv/bin/activate && \
    /home/yoda/venv/bin/pip install -r requirements.txt

WORKDIR /home/yoda

RUN /home/yoda/venv/bin/pip install .
