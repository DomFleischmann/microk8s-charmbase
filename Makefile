build:
	rm -fr lib/juju
	cp -r ../../juju lib/
	# pip3 install --upgrade --target lib/ charmhelpers
clean:
	rm -fr lib/juju

