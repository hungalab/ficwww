install:
	make base_install
	make lighttpd

base_install:
	sudo apt-get update
	sudo apt-get install -y python3 python3-flask lighttpd
	sudo pip3 install flup-py3
	sudo usermod -a -G gpio www-data

lighttpd:
	cd /etc/lighttpd; \
	ln -s /conf-available/10-accesslog.conf ./conf-enabled/.; \
	ln -s /conf-available/10-fastcgi.conf ./conf-enabled/.; \
	ln -s /conf-available/10-rewrite.conf ./conf-enabled/.; \
	cp /var/www/ficwww/deploy/lighttpd/lighttpd.conf ./; \
	cp /var/www/ficwww/deploy/lighttpd/10-fastcgi.conf ./conf-available; \

