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
'''A client for listen-server.

A simple but reasonably complete network client. The priority
is to demonstrate the ease of exchanging messages across network
connections, e.g. requests and responses. At the same time all
network software must also deal with establishment of transports
and the on-going potential for errors.

Notes:
* returning messages based on Faulted (e.g. NotConnected) as the
  application output causes the printing of a diagnostic on stderr
  and an empty stdout.
* pre-defined messages (i.e. Enquiry and Ack/Nak) are used as
  request-response messages to minimize the size of this example.
  Any registered messages (i.e. ar.bind()) can be used.
'''
import ansar.connect as ar

# Where is the server?
class Settings(object):
	def __init__(self, connecting_ipp=None, seconds=None):
		self.connecting_ipp = connecting_ipp or ar.HostPort()
		self.seconds = seconds

SETTINGS_SCHEMA = {
	'connecting_ipp': ar.UserDefined(ar.HostPort),
	'seconds': float,
}

ar.bind(Settings, object_schema=SETTINGS_SCHEMA)

# Procedure is;
# - connect,
# - verify connection,
# - send request,
# - expect response,
# - return the servers response as the output.
# While also dealing with;
# - configuration errors (e.g. network addresses),
# - user intervention, i.e. control-c,
# - missing, incorrect or non-functional server,
# - network problems.

def client(self, settings):
	# Initiate a connection.
	ar.connect(self, settings.connecting_ipp)

	# Verify the connection.
	m = self.select(ar.Connected, ar.NotConnected, ar.Stop)
	if isinstance(m, ar.NotConnected):
		return m
	elif isinstance(m, ar.Stop):
		return ar.Aborted()

	# Send a request.
	# Return address (i.e. self.return_address) for the
	# current Connected message is the remote end of the
	# connection.
	self.send(ar.Enquiry(), self.return_address)

	# Get the response.
	m = self.select(ar.Ack, ar.Nak,		# Server-to-client application messages.
		ar.Abandoned,					# Session management.
		ar.Stop,						# Intervention.
		ar.Other,						# Capture others for diagnostics.
		seconds=settings.seconds)		# Expect response within reasonable time.

	expected = (ar.Ack, ar.Nak)
	if isinstance(m, expected):			# Application message.
		pass
	elif isinstance(m, ar.Abandoned):	# Lost the connection.
		pass
	elif isinstance(m, ar.Stop):		# Intervention.
		return ar.Aborted()
	elif isinstance(m, ar.SelectTimer):	# Server took too long.
		return ar.TimedOut(m)
	else:
		t = ar.tof(m.value)					# Not any of the above.
		a = [ar.tof(e) for e in expected]
		return ar.Rejected(server_response=(t, a))

	return m

ar.bind(client)

#
#
factory_settings = Settings(connecting_ipp=ar.HostPort(host='127.0.0.1', port=5011), seconds=3.0)

if __name__ == '__main__':
	ar.create_object(client, factory_settings=factory_settings)
