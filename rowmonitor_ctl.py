#!/usr/bin/env python
import os
import sys
import signal
import json
from subprocess import Popen

# pid = str(os.getpid())
pidfile = "/tmp/rowmonitor.pid"

config_file = sys.argv[1]
config = json.loads(open(config_file, "r").read())
home_dir = config["working_directory"]
pidfile = "{0}/rowmonitor.pid".format(home_dir)
binfile = "{0}/rowmonitor.py".format(home_dir)

if sys.argv[2] == "start":

    if os.path.isfile(pidfile):
      print "%s already exists, exiting" % pidfile
      sys.exit()

    pid = Popen([binfile, config_file], shell=False).pid

    with open(pidfile, "w") as pid_file:
        pid_file.write(str(pid))

elif sys.argv[2] == "stop":

    if not os.path.isfile(pidfile):
      print "%s does not exist, exiting" % pidfile
      sys.exit()

    pid = int(file(pidfile, 'r').read())
    os.kill(pid, signal.SIGKILL)
    os.unlink(pidfile)

elif sys.argv[2] == "restart":

    if not os.path.isfile(pidfile):
      print "%s does not exist, exiting" % pidfile
      sys.exit()

    pid = int(file(pidfile, 'r').read())
    os.kill(pid, signal.SIGKILL)

    os.unlink(pidfile)

    pid = Popen([binfile, config_file], shell=False).pid
    with open(pidfile, "w") as pid_file:
        pid_file.write(str(pid))
