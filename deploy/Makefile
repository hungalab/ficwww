install:
	make base_install
	make lighttpd

base_install:
	sudo apt-get update
	sudo apt-get install -y git python3 python3-flask lighttpd
	sudo pip3 install flup-py3
	cd /var/www
	git clone http://github.com/hungalab/ficwww
	cd ficwww
	git clone http://github.com/hungalab/libfic2
	cd libfic2
	make clean && make
	cd ../
	ln -s libfic2/pyficlib2.so .

lighttpd:
	cd /etc/lighttpd
	sudo ln -s ./conf-available/10-accesslog.conf ./conf-enabled/.
	sudo ln -s ./conf-available/10-fastcgi.conf ./conf-enabled/.
	sudo ln -s ./conf-available/10-rewrite.conf ./conf-enabled/.
	sudo cp /var/www/ficwww/deploy/lighttpd/lighttpd.conf ./
	sudo cp /var/www/ficwww/deploy/lighttpd/10-fastcgi.conf ./conf-available
