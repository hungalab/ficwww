install:
	make base_install
	make lighttpd

base_install:
	sudo apt-get update
	sudo apt-get install -y python3 python3-flask lighttpd
	sudo pip3 install flup-py3

lighttpd:
	cd /etc/lighttpd
	sudo ln -s ./conf-available/10-accesslog.conf ./conf-enabled/.
	sudo ln -s ./conf-available/10-fastcgi.conf ./conf-enabled/.
	sudo ln -s ./conf-available/10-rewrite.conf ./conf-enabled/.
	sudo cp /var/www/ficwww/deploy/lighttpd/lighttpd.conf ./
	sudo cp /var/www/ficwww/deploy/lighttpd/10-fastcgi.conf ./conf-available
