FROM centos
ENV container docker
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*;\
rm -f /etc/systemd/system/*.wants/*;\
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*;\
rm -f /lib/systemd/system/anaconda.target.wants/*;
RUN yum -y update && yum -y groupinstall development && yum install yum-utils;
RUN yum-builddep -y python;
RUN curl -O https://www.python.org/ftp/python/3.5.1/Python-3.5.1.tgz; 
RUN tar xf Python-3.5.1.tgz;
RUN rm Python-3.5.1.tgz;
RUN yum -y install make;
RUN cd /Python-3.5.1 
RUN ./Python-3.5.1/configure;
RUN make && make install;
RUN cd .. 
RUN pip3 install requests;
RUN pip3 install selenium;
RUN pip3 install Flask;
RUN pip3 install apscheduler;
RUN pip3 install flask-wtf;
RUN yum install -y fontconfig freetype freetype-devel fontconfig-devel libstdc++;
RUN yum install -y wget;
RUN wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.8-linux-x86_64.tar.bz2;
RUN mkdir -p /opt/phantomjs;
RUN tar -xjvf phantomjs-1.9.8-linux-x86_64.tar.bz2 -C /opt/phantomjs/;
RUN ln -s /opt/phantomjs/bin/phantomjs /usr/bin/phantomjs;
COPY ws_parser /home/ws_parser/
COPY services/ws_serv.service /etc/systemd/system/
RUN systemctl enable ws_serv.service;
COPY services/flask_engine.service /etc/systemd/system/
RUN systemctl enable flask_engine.service;

#RUN pip3 install numpy;
#RUN pip3 install scipy;
#RUN pip3 install scikit-learn==0.17.1;
#COPY srv.py /home/
#COPY mos.service /etc/systemd/system/
#COPY clf /home/
#COPY clf_01.npy /home/
#COPY clf_02.npy /home/
#COPY clf_03.npy /home/
#COPY clf_04.npy /home/
#COPY vectorizer /home/
#COPY vectorizer_01.npy /home/
#COPY vectorizer_02.npy /home/
VOLUME [ "/sys/fs/cgroup" ]
CMD ["/usr/sbin/init"]
#RUN systemctl enable mos.service;
