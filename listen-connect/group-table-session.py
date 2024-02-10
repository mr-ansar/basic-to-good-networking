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
'''A client for listen-server using the GroupTable object and the session option.

A copy of group-table.py and similar code except that this time a session value
is passed to the GroupTable object.

Ths big difference here is that the session object is a "pure application"
object, i.e. it is not infected with any networking details. It has all the
address information accumulated by GroupTable (passed as the group parameter)
and can immediately begin whatever interactions it needs to carry out.
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

# The much simplified client, created at the
# moment GroupTable determines that all address
# information is in place.
def client(self, group):
	m = self.ask(ar.Enquiry(), (ar.Ack, ar.Nak, ar.Stop), group.server, seconds=3.0)

	expected = (ar.Ack, ar.Nak)
	if isinstance(m, expected):
		pass
	elif isinstance(m, ar.Stop):		# Errors, completions and intervention.
		return ar.Aborted()
	else:
		return ar.TimedOut(m)			# SelectTimer.
	return m

ar.bind(client)

# A client that uses a GroupTable to manage a
# collection of connections (i.e. one) and create
# a session when the connections are in place.
READY_OR_NOT = 30.0

def main(self, settings):
	# Describe the group.
	group = ar.GroupTable(
		server=ar.CreateFrame(ar.ConnectToAddress, settings.connecting_ipp)
	)

	# Describe the session.
	session = ar.CreateFrame(client)

	# Start the group engine.
	a = group.create(self, seconds=READY_OR_NOT, session=session)
	m = self.select(ar.Completed, ar.Stop)

	# Wait for its completion.
	if isinstance(m, ar.Completed):
		return m.value

	# Or intervention.
	self.send(ar.Stop(), a)
	self.select(ar.Completed)
	return ar.Aborted()

ar.bind(main)

#
#
factory_settings = Settings(connecting_ipp=ar.HostPort(host='127.0.0.1', port=5011), seconds=30.0)

if __name__ == '__main__':
	ar.create_object(main, factory_settings=factory_settings)
