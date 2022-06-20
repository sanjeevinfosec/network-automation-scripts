#!/usr/bin/python3
# Copyright(C) 2009  Glen Pitt-Pladdy
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or(at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#
#

#
# Added SSL-Skip for a special scenario where a web server is delivering
# the status page on localhost with a self-signed certificate
#
import os
import time
import urllib.request
# import ssl to skip self-signed certificate
import ssl

cachetime = 30
cachefile = "/var/cache/librenms/apache-snmp"

# Check for a cache file newer than cachetime seconds ago

if os.path.isfile(cachefile) and (time.time() - os.stat(cachefile)[8]) < cachetime:
    with open(cachefile, "r") as f:
        data = f.read()
else:
    # Set parameters to skip SSL checks
    # for localhost + self-signed cert
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Grab the status URL (fresh data), needs package urllib3
    data = (
        urllib.request.urlopen("http://localhost/server-status?auto", context=context)
        .read()
        .decode("UTF-8")
    )
    with open(f"{cachefile}.TMP.{str(os.getpid())}", "w") as f:
        f.write(data)
    os.rename(f"{cachefile}.TMP.{str(os.getpid())}", cachefile)


# dice up the data
scoreboardkey = ["_", "S", "R", "W", "K", "D", "C", "L", "G", "I", "."]
params = {}
for line in data.splitlines():
    fields = line.split(": ")
    if len(fields) <= 1:
        continue  # "localhost" as first line causes out of index error
    elif fields[0] == "Scoreboard":
        # count up the scoreboard into states
        states = {state: 0 for state in scoreboardkey}
        for state in fields[1]:
            states[state] += 1
    elif fields[0] == "Total kBytes":
        # turn into base(byte) value
        params[fields[0]] = int(fields[1]) * 1024
    else:
        # just store everything else
        params[fields[0]] = fields[1]

# output the data in order(this is because some platforms don't have them all)
dataorder = [
    "Total Accesses",
    "Total kBytes",
    "CPULoad",
    "Uptime",
    "ReqPerSec",
    "BytesPerSec",
    "BytesPerReq",
    "BusyWorkers",
    "IdleWorkers",
]
for param in dataorder:
    try:
        print(params[param])
    except KeyError:  # not all Apache's have all stats
        print("U")

# print the scoreboard
for state in scoreboardkey:
    print(states[state])
