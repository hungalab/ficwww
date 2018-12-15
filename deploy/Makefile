install:
	make base_install
	make setup_ficlib2
	make setup_lighttpd

base_install:
	apt-get update
	apt-get install -y python3 python3-flask python3-pip lighttpd
	pip3 install flup-py3
	usermod -a -G gpio www-data

setup_lighttpd:
	cd /etc/lighttpd/conf-enabled; \
	ln -s ../conf-available/10-accesslog.conf .; \
	ln -s ../conf-available/10-rewrite.conf .; \
	ln -s ../conf-available/10-ficwww.conf .; \
	cd ../ ; \
	mv lighttpd.conf lighttpd.conf.orig
	ln -s /var/www/ficwww/deploy/lighttpd/ficwww-lighttpd.conf /etc/lighttpd/lighttpd.conf; \
	ln -s /var/www/ficwww/deploy/lighttpd/10-ficwww.conf /etc/lighttpd/conf-available/.; \

setup_ficlib2:
	git clone https://github.com/hungalab/libfic2.git
	cd libfic2 && make
	ln -s libfic2/pyficlib2.so .

update:
	git pull
	cd libfic2 && git pull && make clean && make