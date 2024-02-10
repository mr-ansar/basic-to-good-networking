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
'''A FSM client for either basic-listen-server or fsm-listen-server.

A copy of basic-connect-client except this version replaces the
use of a function object with a finite state machine, "def client"
becomes "class Client".

Essential actions of the 3-state machine;
* INITIAL - receive Start, call connect(), shift to STARTING
* STARTING - receive Connected, send Enquiry, shift to RUNNING
* RUNNING - receive Ack, complete

Refer below and to basic-connect-client.py for further notes.
.
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

class INITIAL: pass
class STARTING: pass
class RUNNING: pass

class Client(ar.Point, ar.StateMachine):
	def __init__(self, settings):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.settings = settings
		self.connected = None
		self.expected = (ar.Ack, ar.Nak)

def Client_INITIAL_Start(self, message):				# Initiate connection.
	ar.connect(self, self.settings.connecting_ipp)
	return STARTING

def Client_STARTING_Connected(self, message):			# Verify connection.
	self.connected = message

	self.send(ar.Enquiry(), self.return_address)		# Send request.
	if self.settings.seconds:
		self.start(ar.T1, self.settings.seconds)		# Add timer.
	return RUNNING

def Client_STARTING_NotConnected(self, message):
	self.complete(message)

def Client_STARTING_Stop(self, message):
	self.complete(ar.Aborted())

def Client_RUNNING_Ack(self, message):					# Receive server response.
	self.complete(message)			

def Client_RUNNING_Nak(self, message):
	self.complete(message)

def Client_RUNNING_Abandoned(self, message):			# Network problems.
	self.complete(message)

def Client_RUNNING_Stop(self, message):					# Intervention.
	self.complete(ar.Aborted())

def Client_RUNNING_T1(self, message):					# Server too slow.
	t = ar.TimedOut(message)
	self.complete(t)

def Client_RUNNING_Unknown(self, message):
	t = ar.tof(message)
	a = [ar.tof(e) for e in self.expected]
	r = ar.Rejected(server_response=(t, a))				# None of the above.
	self.complete(r)

CLIENT_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	STARTING: (
		(ar.Connected, ar.NotConnected, ar.Stop), ()
	),
	RUNNING: (
		(ar.Ack, ar.Nak, ar.Abandoned, ar.Stop, ar.T1, ar.Unknown), ()
	),
}

ar.bind(Client, CLIENT_DISPATCH)

#
#
factory_settings = Settings(connecting_ipp=ar.HostPort(host='127.0.0.1', port=5012), seconds=3.0)

if __name__ == '__main__':
	ar.create_object(Client, factory_settings=factory_settings)
