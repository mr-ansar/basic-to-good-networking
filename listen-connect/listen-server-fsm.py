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
'''A FSM server that supports an Enquiry-Ack exchange with clients.

A copy of listen-server except this version replaces the
use of a function object with a finite state machine, i.e. "def server"
becomes "class Server".

Essential actions of the 3-state machine;
* INITIAL - receive Start, call listen(), shift to STARTING
* STARTING - receive Listening, shift to RUNNING
* RUNNING - receive Accepted, shift to RUNNING
* RUNNING - receive Enquiry, send Ack, shift to RUNNING
* RUNNING - receive Stop, complete

Refer below and to basic-listen-server.py for further notes.
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

#
#
class INITIAL: pass
class STARTING: pass
class RUNNING: pass

class Server(ar.Point, ar.StateMachine):
	def __init__(self, settings):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.settings = settings
		self.listening = None
		self.expected = (ar.Enquiry,)

def Server_INITIAL_Start(self, message):				# Open the port.
	ar.listen(self, self.settings.listening_ipp)
	return STARTING

def Server_STARTING_Listening(self, message):			# Verify port.
	self.listening = message
	return RUNNING

def Server_STARTING_NotListening(self, message):
	self.complete(message)

def Server_STARTING_Stop(self, message):
	self.complete(message)

def Server_RUNNING_Enquiry(self, message):				# Receive client request.
	self.reply(ar.Ack())								# Send response.
	return RUNNING

def Server_RUNNING_Accepted(self, message):				# Session management.
	t = ar.tof(message)
	self.console(f'Session <{t}> at {self.return_address}')
	return RUNNING

def Server_RUNNING_Abandoned(self, message):
	t = ar.tof(message)
	self.console(f'Session <{t}> at {self.return_address}')
	return RUNNING

def Server_RUNNING_NotAccepted(self, message):			# Network problems.
	self.complete(message)

def Server_RUNNING_NotListening(self, message):
	self.complete(message)

def Server_RUNNING_Stop(self, message):					# Intervention.
	self.complete(ar.Aborted())

def Server_RUNNING_Unknown(self, message):
	t = ar.tof(message)
	a = [ar.tof(e) for e in self.expected]
	s = ar.Rejected(client_request=(t, a))
	self.warning(s)
	return RUNNING

SERVER_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	STARTING: (
		(ar.Listening, ar.NotListening, ar.Stop), ()
	),
	RUNNING: (
		(ar.Enquiry, ar.Accepted, ar.Abandoned, ar.NotAccepted, ar.NotListening, ar.Stop, ar.Unknown), ()
	),
}

ar.bind(Server, SERVER_DISPATCH)

#
#
factory_settings = Settings(ar.HostPort('127.0.0.1', 5012))

if __name__ == '__main__':
	ar.create_object(Server, factory_settings=factory_settings)
