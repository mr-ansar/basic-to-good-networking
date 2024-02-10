# Author: Scott Woods <scott.18.ansar@gmail.com.com>
# MIT License
#
# Copyright (c) 2022
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

# Development environment for a simple TCP service at a fixed port and a
# matching client. The client sends a query and the server responds with
# an acknowledgement. The client then terminates with an appropriate message,
# e.g. the response from the server.

# Normal use;
# $ make clean build home
# $ make start
# $ make
# $ make
# ..
# Clean-build-home creates fresh executables and loads them into a
# brand new environment. A "make start" initiates the "back end"
# i.e. the server process that listens on a fixed port. With the
# back end up and running its possible to use "make" any number of
# times with the option of editing the source code of the client or
# server between each run. The make rule will auto-compile, deploy
# the updated executables into the current environment and stop/start
# processes as necessary (e.g. the server). This is a useful
# edit-run-debug cycle in a multi-processing scenario.
all: run

# Useful lists of file names relating to executables
#
EXECUTABLES := listen-server listen-server-fsm listen-server-session \
connect-client connect-client-ask connect-client-fsm connect-client-session \
connect-to-address group-table group-table-session ansar-group
BUILD := $(EXECUTABLES:%=dist/%)
SPEC := $(EXECUTABLES:%=%.spec)

# Default rule to turn a python script into an executable.
#
dist/% : %.py
	pyinstaller --onefile --log-level ERROR -p . $<

dist/ansar-group:
	pyinstaller --onefile --log-level ERROR -p . `which ansar-group`

clean::
	-rm -rf build dist $(SPEC)

#
#
build:: $(BUILD)

#
#
home:
	ansar create
	ansar deploy dist
	ansar add listen-server server
	ansar add listen-server-fsm server-fsm
	ansar add listen-server-session server-session
	ansar add connect-client client
	ansar add connect-client-ask ask
	ansar add connect-client-fsm client-fsm
	ansar add connect-client-session client-session
	ansar add connect-to-address connect-to-address
	ansar add group-table group-table
	ansar add group-table-session group-table-session
	ansar run --group-name=front-end --create-group
	ansar run --group-name=back-end --create-group
	ansar run --group-name=ask --create-group
	ansar run --group-name=fsm --create-group
	ansar run --group-name=session --create-group
	ansar run --group-name=connect-to-address --create-group
	ansar run --group-name=group-table --create-group
	ansar run --group-name=group-table-session --create-group
	ansar update group.front-end --main-role=client
	ansar update group.ask --main-role=ask
	ansar update group.fsm --main-role=client-fsm
	ansar update group.session --main-role=client-session
	ansar update group.connect-to-address --main-role=connect-to-address
	ansar update group.group-table --main-role=group-table
	ansar update group.group-table-session --main-role=group-table-session

clean::
	-ansar --force destroy

# Initiate the backend.
start:
	ansar start server server-fsm server-session --group-name=back-end

# Terminate the backend.
stop:
	ansar stop back-end

# Update the environment as required and
# execute the client within the current shell,
# i.e. directing all logging to stderr.
# The run should complete with the message
# received from the server in response to the
# clients request.
run: build
	@ansar --debug-level=CONSOLE --force deploy dist
	@ansar --debug-level=CONSOLE run client --group-name=front-end

fsm: build
	@ansar --debug-level=CONSOLE --force deploy dist
	@ansar --debug-level=CONSOLE run client-fsm --group-name=fsm

session: build
	@ansar --debug-level=CONSOLE --force deploy dist
	@ansar --debug-level=CONSOLE run client-session --group-name=session

ask: build
	@ansar --debug-level=CONSOLE --force deploy dist
	@ansar --debug-level=CONSOLE run ask --group-name=ask

connect-to-address: build
	@ansar --debug-level=CONSOLE --force deploy dist
	@ansar --debug-level=DEBUG run connect-to-address --group-name=connect-to-address

group-table: build
	@ansar --debug-level=CONSOLE --force deploy dist
	@ansar --debug-level=DEBUG run group-table --group-name=group-table

group-table-session: build
	@ansar --debug-level=CONSOLE --force deploy dist
	@ansar --debug-level=DEBUG run group-table-session --group-name=group-table-session
