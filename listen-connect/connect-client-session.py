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
'''A session-based client for either basic-listen-server, fsm-listen-server or session-listen-server.

A copy of basic-connect-client except this version uses a pair of
finite state machine classes, i.e. a controller class that manages
sessions and a session class.

Essential actions of the 2-state session machine (ClientSession);
* INITIAL - receive Start, send Enquiry, shift to RUNNING
* RUNNING - receive Ack, complete

Essential actions of the 3-state controller machine (Client);
* INITIAL - receive Start, call connect(), shift to STARTING
* STARTING - receive Connected, shift to RUNNING
* RUNNING - receive Closed, complete

The create_object() function is used to create an instance of the Client.
The Client initiates the connection and then moves to a monitoring role,
receiving notifications when session objects are created (Connected) and
destroyed (Closed/Abandoned).

Instances of the ClientSession object are created by the sockets machinery
for every connected client. Session objects do not receive any of the
session management or network error messages, leaving them to focus on
the message exchange between client and server. Session objects terminate
either by their own completion or when they receive a Stop. These events
result in Closed and Abandoned messages being sent to the controller,
respectively.

Refer below and to basic-connect-client.py for further notes.
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

# Session for the connecting end.
# Instantiated by the sockets subsystem at the moment
# a transport is successfully established, as directed
# by the "connect()" call in the controller object below.
# The server session is available at "remote_address".
class INITIAL: pass
class STARTING: pass
class RUNNING: pass
class ENQUIRED: pass

class ClientSession(ar.Point, ar.StateMachine):
	def __init__(self, seconds, remote_address=None, **kv):		# Connection is verified.
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.seconds = seconds						# Save values needed during the
		self.remote_address = remote_address		# life of the session.
		self.expected = (ar.Ack, ar.Nak)

def ClientSession_INITIAL_Start(self, message):
	self.send(ar.Enquiry(), self.remote_address)	# Send the request.
	if self.seconds:
		self.start(ar.T1, self.seconds)				# Start timer.
	return ENQUIRED

def ClientSession_ENQUIRED_Ack(self, message):		# Receive server response.
	self.complete(message)

def ClientSession_ENQUIRED_Nak(self, message):
	self.complete(message)

def ClientSession_ENQUIRED_Stop(self, message):		# Session is being terminated, e.g. Abandoned.
	self.complete(ar.Aborted())

def ClientSession_ENQUIRED_T1(self, message):		# Server took too long.
	t = ar.TimedOut(message)
	self.complete(t)

def ClientSession_ENQUIRED_Unknown(self, message):	# None of the above.
	t = ar.tof(message)
	a = [ar.tof(e) for e in self.expected]
	r = ar.Rejected(server_response=(t, a))
	self.complete(r)

CLIENT_SESSION_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	ENQUIRED: (
		(ar.Ack, ar.Nak, ar.Stop, ar.T1, ar.Unknown), ()
	),
}

ar.bind(ClientSession, CLIENT_SESSION_DISPATCH)

# Controller for the connecting end.
# Session management and network problems,
# instantiated by create_object().
class Client(ar.Point, ar.StateMachine):
	def __init__(self, settings):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.settings = settings
		self.connected = None

def Client_INITIAL_Start(self, message):
	session = ar.CreateFrame(ClientSession, self.settings.seconds)
	ar.connect(self, self.settings.connecting_ipp, session=session)
	return STARTING

def Client_STARTING_Connected(self, message):
	self.connected = message
	return RUNNING

def Client_STARTING_NotConnected(self, message):
	self.complete(message)

def Client_STARTING_Stop(self, message):
	self.complete(ar.Aborted())

def Client_RUNNING_Closed(self, message):
	# Session has completed. Terminate this controller passing
	# the session value as the completion value for this machine.
	self.complete(message.value)

def Client_RUNNING_Abandoned(self, message):
	# Session was interrupted
	self.complete(message)

def Client_RUNNING_Stop(self, message):
	self.complete(message)

CLIENT_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	STARTING: (
		(ar.Connected, ar.NotConnected, ar.Stop), ()
	),
	RUNNING: (
		(ar.Closed, ar.Abandoned, ar.Stop), ()
	),
}

ar.bind(Client, CLIENT_DISPATCH)

#
#
factory_settings = Settings(connecting_ipp=ar.HostPort(host='127.0.0.1', port=5013), seconds=3.0)

if __name__ == '__main__':
	ar.create_object(Client, factory_settings=factory_settings)
