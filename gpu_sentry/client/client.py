# -*- coding: utf-8 -*-
#
# MIT License
#
# Copyright (c) 2019 Grzegorz Jacenków
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

"""Client-side application logic, i.e. monitoring GPU instances."""

import os
import socket

from pynvml import (
    NVMLError,
    nvmlDeviceGetCount,
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetName,
    nvmlInit,
)

from twisted.internet import task, reactor
import requests

import client_config as config


def _convert_kb_to_gb(size):
    """Convert given size in kB to GB with 2-decimal places rounding."""
    return round(size / 1024 ** 3, 2)


def get_process_info():
    smi_output = os.popen('nvidia-smi').read()
    """
    ...
+-----------------------------------------------------------------------------+
| Processes:                                                                  |
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
|        ID   ID                                                   Usage      |
|=============================================================================|
|    0   N/A  N/A      1425      G   /usr/lib/xorg/Xorg                  9MiB |
|    0   N/A  N/A      1803      G   /usr/bin/gnome-shell                3MiB |
|    1   N/A  N/A      1425      G   /usr/lib/xorg/Xorg                  4MiB |
|    2   N/A  N/A      1425      G   /usr/lib/xorg/Xorg                  4MiB |
|    3   N/A  N/A      1425      G   /usr/lib/xorg/Xorg                  4MiB |
+-----------------------------------------------------------------------------+
(There's a newline at the end of the output)
    """
    gpuid_to_pids = dict()
    pids = set()  # one process may utilize many gpus
    for line in smi_output[smi_output.rindex('='):].split('\n')[1:-2]:
        if 'No running processes found' in line:
            continue
        tmp = line.split()
        if len(tmp)==1:
            continue
        gpu_id, pid = tmp[1], tmp[4]
        pids.add(pid)
        if gpu_id in gpuid_to_pids.keys():
            gpuid_to_pids[gpu_id].append(pid)
        else:
            gpuid_to_pids[gpu_id] = [pid]
    if len(pids) == 0:
        return dict()
    process_output = os.popen(
        f"ps -p {','.join(pids)} -o pid,vsz=MEMORY -o user,group=GROUP -o comm,args=ARGS").read().split('\n')[1:-1]
    """
> ps -p 1803,1425 -o pid,vsz=MEMORY -o user,group=GROUP -o comm,args=ARGS
PID MEMORY USER     GROUP    COMMAND         ARGS
1425 25383856 root   root     Xorg            /usr/lib/xorg/Xorg vt1 -displayfd 3 -auth /run/user/125/gdm/Xauthority -b
1803 3474132 gdm     gdm      gnome-shell     /usr/bin/gnome-shell
    """
    processes = dict()
    for line in process_output:
        tmp = line.strip().split(maxsplit=5)
        pid, memory, user, command, args = tmp[0], tmp[1], tmp[2], tmp[4], tmp[5]
        # if 'xorg' in command.lower():
        #     continue
        processes[pid] = f'{pid}: {command} {args}'

    output = dict()
    for gpu_id, pids in gpuid_to_pids.items():
        output[gpu_id] = [processes[pid] for pid in pids]

    return output


def get_statistics():
    """Get statistics for each GPU installed in the system."""
    nvmlInit()
    statistics = []
    try:
        count = nvmlDeviceGetCount()
        process_info = get_process_info()
        for i in range(count):
            handle = nvmlDeviceGetHandleByIndex(i)

            memory = nvmlDeviceGetMemoryInfo(handle)

            statistics.append({
                "gpu": i,
                "name": nvmlDeviceGetName(handle).decode("utf-8"),
                "memory": {
                    "total": _convert_kb_to_gb(int(memory.total)),
                    "used": _convert_kb_to_gb(int(memory.used)),
                    "utilization": int(memory.used / memory.total * 100)
                },
                "processes": process_info.get(str(i), []),
            })
    except NVMLError as error:
        print(error)

    return statistics


def send_statistics():
    """Send statistics to the server-side API."""
    # try:
    host = socket.gethostname()

    requests.post(config.SERVER_URL,
                    json={"hostname": host,
                        "statistics": get_statistics()})
    print("Statistics sent.")
    # except Exception as err:
    #     print("An error occurred while sending statistics: ", err)


def run_client():
    """Run client to send statistics periodically."""
    l = task.LoopingCall(send_statistics)
    l.start(config.CLIENT_TIMEOUT)

    reactor.run()


if __name__ == '__main__':
    run_client()
