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
'''A server that supports an Enquiry-Ack exchange with clients.

A simple but reasonably complete network server. The priority
is to demonstrate the ease of exchanging messages across network
connections, e.g. requests and responses. At the same time all
network software must also deal with establishment of sessions
and the on-going potential for errors.

Notes:
* returning messages based on Faulted (e.g. NotListening) as the
  final output, causes the printing of a diagnostic on stderr and an
  empty stdout.
* pre-defined messages (i.e. Enquiry and Ack/Nak) are used as
  request-response messages to minimize the size of this example.
  Any registered messages (i.e. ar.bind()) can be used.
'''
import ansar.connect as ar

# Where to setup.
class Settings(object):
	def __init__(self, listening_ipp=None):
		self.listening_ipp = listening_ipp or ar.HostPort()

SETTINGS_SCHEMA = {
	'listening_ipp': ar.UserDefined(ar.HostPort),
}

ar.bind(Settings, object_schema=SETTINGS_SCHEMA)

# Procedure is;
# - open the network port,
# - verify port is open,
# - expect session events,
# - and expect requests,
# - respond to requests
# While also dealing with;
# - configuration errors (e.g. network addresses),
# - user intervention, i.e. control-c,
# - missing, incorrect or non-functional clients,
# - network problems.

def server(self, settings):
	# Open the port.
	ar.listen(self, settings.listening_ipp)

	# Verify port.
	m = self.select(ar.Listening, ar.NotListening, ar.Stop)
	if not isinstance(m, ar.Listening):
		return m

	# Accept sessions, receive client messages,
	# detect network problems and intervention.
	while True:
		m = self.select(ar.Enquiry,				# Client-to-server application message.
			ar.Accepted, ar.Abandoned,			# Session management.
			ar.NotAccepted, ar.NotListening,	# Network problems.
			ar.Stop,							# Intervention.
			ar.Other)							# Capture others for diagnostics.

		expected = (ar.Enquiry,)
		if isinstance(m, expected):				# Application message.
			pass
		elif isinstance(m, (ar.Accepted, ar.Abandoned)):				# Session management.
			t = ar.tof(m)
			self.console(f'Session <{t}> at {self.return_address}')
			continue
		elif isinstance(m, (ar.NotAccepted, ar.NotListening)):			# Network problems.
			return m
		elif isinstance(m, ar.Stop):			# Intervention.
			return ar.Aborted()
		elif isinstance(m, ar.Other):			# None of the above.
			t = ar.tof(m.value)
			a = [ar.tof(e) for e in expected]
			s = ar.Rejected(client_request=(t, a))
			self.warning(s)
			continue

		self.reply(ar.Ack())

ar.bind(server)

#
#
factory_settings = Settings(ar.HostPort('127.0.0.1', 5011))

if __name__ == '__main__':
	ar.create_object(server, factory_settings=factory_settings)
