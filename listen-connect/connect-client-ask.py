# Author: Scott Woods <scott.18.ansar@gmail.com.com>
# MIT License
#
# Copyright (c) 2017-2024 Scott Woods
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
'''A synchronous client for listen-server.

A copy of connect-client except this version uses the blocking/synchronous
option (i.e. ask) for the request-reponse exchange.

Refer to connect-client.py and Makefile for further notes.
'''
import ansar.connect as ar

class Settings(object):
	def __init__(self, connecting_ipp=None, seconds=None):
		self.connecting_ipp = connecting_ipp or ar.HostPort()
		self.seconds = seconds

SETTINGS_SCHEMA = {
	'connecting_ipp': ar.UserDefined(ar.HostPort),
	'seconds': float,
}

ar.bind(Settings, object_schema=SETTINGS_SCHEMA)

def client(self, settings):
	ar.connect(self, settings.connecting_ipp)

	m = self.select(ar.Connected, ar.NotConnected, ar.Stop)
	if isinstance(m, ar.NotConnected):
		return m
	elif isinstance(m, ar.Stop):
		return ar.Aborted()

	# Send a request and expect a response.
	m = self.ask(ar.Enquiry(),
		(ar.Ack, ar.Nak, ar.Abandoned, ar.Stop, ar.Other),
		self.return_address, seconds=settings.seconds)

	expected = (ar.Ack, ar.Nak)
	if isinstance(m, expected):
		pass
	elif isinstance(m, ar.Abandoned):
		pass
	elif isinstance(m, ar.Stop):
		return ar.Aborted()
	elif isinstance(m, ar.SelectTimer):
		return ar.TimedOut(m)
	else:
		t = ar.tof(m.value)
		a = [ar.tof(e) for e in expected]
		return ar.Rejected(server_response=(t, a))

	return m

ar.bind(client)

#
#
factory_settings = Settings(connecting_ipp=ar.HostPort(host='127.0.0.1', port=5011), seconds=3.0)

if __name__ == '__main__':
	ar.create_object(client, factory_settings=factory_settings)
