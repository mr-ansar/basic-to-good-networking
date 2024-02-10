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
'''A session-based server that supports an Enquiry-Ack exchange with clients.

A copy of listen-server and listen-server-fsm except this
version uses a pair of finite state machine classes, i.e. a controller
class that manages sessions and a session class.

Essential actions of the 2-state session machine (Session);
* INITIAL - receive Start, shift to RUNNING
* RUNNING - receive Enquiry, send Ack, shift to RUNNING
* RUNNING - receive Stop, complete

Essential actions of the 3-state controller machine (Server);
* INITIAL - receive Start, call listen(), shift to STARTING
* STARTING - receive Listening, shift to RUNNING
* RUNNING - receive Accepted, shift to RUNNING
* RUNNING - receive Stop, complete

The create_object() function is used to create an instance of the Server.
The Server establishes the listen and then moves to a monitoring role,
receiving notifications when session objects are created (Accepted) and
destroyed (Closed/Abandoned).

Instances of the Session object are created by the sockets machinery
for every accepted client. Session objects do not receive any of the
session management or network error messages, leaving them to focus on
the message exchange between client and server. Session objects terminate
either by their own completion or when they receive a Stop. These events
result in Closed and Abandoned messages being sent to the controller,
respectively.

Refer to basic-listen-server.py for further notes.
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

# Accepting end of a session.
# Instantiated by the sockets subsystem at the moment
# a transport is successfully established, as directed
# by the "listen()" call and passing the "session=session"
# argument.
# The client is available at "remote_address".
class INITIAL: pass
class STARTING: pass
class RUNNING: pass

class Session(ar.Point, ar.StateMachine):
	def __init__(self, **kv):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.expected = (ar.Enquiry,)

def Session_INITIAL_Start(self, message):
	return RUNNING

def Session_RUNNING_Enquiry(self, message):
	self.reply(ar.Ack())
	return RUNNING

def Session_RUNNING_Stop(self, message):
	self.complete(message)

def Session_RUNNING_Unknown(self, message):
	t = ar.tof(message)
	a = [ar.tof(e) for e in self.expected]
	s = ar.Rejected(client_request=(t, a))
	self.warning(s)
	return RUNNING

SESSION_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	RUNNING: (
		(ar.Enquiry, ar.Stop, ar.Unknown), ()
	),
}

ar.bind(Session, SESSION_DISPATCH)

# Session management and network problems,
# instantiated by create_object().
class Server(ar.Point, ar.StateMachine):
	def __init__(self, settings):
		ar.Point.__init__(self)
		ar.StateMachine.__init__(self, INITIAL)
		self.settings = settings
		self.listening = None

def Server_INITIAL_Start(self, message):
	session = ar.CreateFrame(Session)
	ar.listen(self, self.settings.listening_ipp, session=session)
	return STARTING

def Server_STARTING_Listening(self, message):
	self.listening = message
	return RUNNING

def Server_STARTING_NotListening(self, message):
	self.complete(message)

def Server_STARTING_Stop(self, message):
	self.complete(message)

def Server_RUNNING_Accepted(self, message):
	t = ar.tof(message)
	self.console(f'Session <{t}> at {self.return_address}')
	return RUNNING

def Server_RUNNING_Abandoned(self, message):
	t = ar.tof(message)
	self.console(f'Session <{t}> at {self.return_address}')
	return RUNNING

def Server_RUNNING_NotAccepted(self, message):
	self.complete(message)

def Server_RUNNING_NotListening(self, message):
	self.complete(message)

def Server_RUNNING_Stop(self, message):
	self.complete(ar.Aborted())

SERVER_DISPATCH = {
	INITIAL: (
		(ar.Start,), ()
	),
	STARTING: (
		(ar.Listening, ar.NotListening, ar.Stop), ()
	),
	RUNNING: (
		(ar.Accepted, ar.Abandoned, ar.NotAccepted, ar.NotListening, ar.Stop), ()
	),
}

ar.bind(Server, SERVER_DISPATCH)

#
#
factory_settings = Settings(ar.HostPort('127.0.0.1', 5013))

if __name__ == '__main__':
	ar.create_object(Server, factory_settings=factory_settings)
