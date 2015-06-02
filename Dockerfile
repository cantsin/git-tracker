FROM ubuntu
MAINTAINER James Tranovich
RUN echo "deb http://archive.ubuntu.com/ubuntu/ $(lsb_release -sc) main universe" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y git python python-dev python3.4 python3.4-dev python3-pip libffi-dev cmake
# manually install libgit2 -- the ubuntu repos are behind.
RUN git clone https://github.com/libgit2/libgit2/ /usr/src/libgit2
RUN cd /usr/src/libgit2 && git checkout tags/v0.22.1
RUN mkdir /usr/src/libgit2/build && cd /usr/src/libgit2/build && cmake .. -DCMAKE_INSTALL_PREFIX=/usr/ && cmake --build . && cmake --build . --target install
# git-tracker.
RUN git clone https://github.com/cantsin/git-tracker /git-tracker
RUN pip3 install -r /git-tracker/requirements.txt
EXPOSE 80
WORKDIR /git-tracker
CMD python3.4 app.py 80
