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
'''A client for listen-server using the GroupTable object.

A functional duplication of connect-client.py and similar code except
that the GroupTable object is used to manage an instance of
ConnectToAddress (see connect-to-address.py).

The GroupTable object is a response to the need to arrange for multiple
objects. It assumes that each object specified in a table eventually
delivers an address. The parent is advised of progress.

Notes:
* The connect() call is replaced with group.create().
* Addresses are accumulated in the group object courtesy of updates.
* the Ready message indicates a full complement of addresses.
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

# A client that uses a GroupTable to manage a
# collection of connections (i.e. one) and generate
# a stream of update and status messages.
READY_OR_NOT = 30.0

def client(self, settings):
	# Describe the group.
	group = ar.GroupTable(
		server=ar.CreateFrame(ar.ConnectToAddress, settings.connecting_ipp)
	)

	# Start the group engine.
	a = group.create(self, seconds=READY_OR_NOT)

	def stop_group():
		self.send(ar.Stop(), a)
		self.select(ar.Completed)

	# Verify everything ready, i.e. connection established.
	while True:
		m = self.select(ar.GroupUpdate, ar.Ready, ar.Completed, ar.Stop)

		if isinstance(m, ar.GroupUpdate):		# Address information. Loop for more.
			group.update(m)
		elif isinstance(m, ar.Ready):			# Full set of addresses. Pop out of loop.
			break
		elif isinstance(m, ar.Completed):		# Group exhausted. Pop out of object.
			return m.value
		elif isinstance(m, ar.Stop):			# Intervention.
			stop_group()
			return ar.Aborted()

	# The actual application code. Send the request
	# and expect a respones.
	self.send(ar.Enquiry(), group.server)

	# Get the response.
	m = self.select(ar.Ack, ar.Nak,		# Server-to-client application messages.
		ar.NotReady,					# Session management.
		ar.Completed,					# Group self-terminated.
		ar.Stop,						# Intervention.
		seconds=settings.seconds)		# Expect response within reasonable time.

	expected = (ar.Ack, ar.Nak)
	if isinstance(m, expected):			# Application message.
		stop_group()
	elif isinstance(m, ar.NotReady):	# Lost the "ready" status. Probably clearing but...
		stop_group()
		return m
	elif isinstance(m, ar.Completed):	# Group self-terminated.
		return m.value
	elif isinstance(m, ar.Stop):		# Intervention.
		stop_group()
		return ar.Aborted()
	else:								# SelectTimer. Server took too long.
		stop_group()
		return ar.TimedOut(m)

	return m

ar.bind(client)

#
#
factory_settings = Settings(connecting_ipp=ar.HostPort(host='127.0.0.1', port=5011), seconds=3.0)

if __name__ == '__main__':
	ar.create_object(client, factory_settings=factory_settings)
