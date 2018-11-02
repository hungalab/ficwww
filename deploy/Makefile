install:
	make base_install
	make lighttpd

base_install:
	sudo apt-get update
	sudo apt-get install -y python3 python3-flask lighttpd
	sudo pip3 install flup-py3
	sudo usermod -a -G gpio www-data

lighttpd:
	cd /etc/lighttpd/conf-enabled; \
	ln -s ../conf-available/10-accesslog.conf .; \
	ln -s ../conf-available/10-rewrite.conf .; \
	cd ../ ; \
	mv lighttpd.conf lighttpd.conf.orig
	ln -s /var/www/ficwww/deploy/lighttpd/ficwww-lighttpd.conf /etc/lighttpd/lighttpd.conf; \
	ln -s /var/www/ficwww/deploy/lighttpd/10-ficwww.conf /etc/lighttpd/conf-available/.; \

