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

"""Server-side application logic, i.e. the Flask server."""

import datetime
import copy

from flask import Flask, json, render_template, request

import server_config as config

app = Flask(__name__)
data = {

}


def process_data(data):
    processed = {'device_details': [],
                 'device_status': {
                     'free': [],
                     'mixed': [],
                     'in_use': []
                 },
                 }
    details = []
    for host, report in data.items():
        info = copy.deepcopy(report)

        info['host'] = host
        info['num_gpus'] = len(info['statistics'])
        info['num_free_gpus'] = len(list(filter(lambda gpu: gpu['memory']['used'] < 1,
                                                info['statistics'])))
        for gpu in info['statistics']:
            gpu['processes'] = list(filter(lambda p: ('gnome' not in p) and ('xorg' not in p), gpu['processes']))
        details.append(info)
    processed['device_details'] = sorted(details, key=lambda x: x['name'])  # sort by name

    device_status = processed['device_status']
    for info in processed['device_details']:
        num_free, num_gpus = info['num_free_gpus'], info['num_gpus']
        if num_free == num_gpus:
            device_status['free'].append(info)
        elif num_free == 0:
            device_status['in_use'].append(info)
        else:
            device_status['mixed'].append(info)
    return processed


@app.route("/", methods=["GET"])
def index():
    """Render the main page after calling the root path."""
    return render_template("index.html", data=process_data(data))


@app.route("/api", methods=["POST"])
def api():
    """Listen for incoming GPU statistics."""
    content = request.json
    # Update the statistics if the client is allowed to POST.
    hostname = content['hostname']
    if hostname in config.PERMIT_CLIENTS.keys():
        data[hostname] = {
            "name": config.PERMIT_CLIENTS[hostname]['name'],
            "statistics": content['statistics'],
            "timestamp": datetime.datetime.now().strftime("%d %B %Y %I:%M%p")
        }
        print(data[hostname])

    return json.dumps(
        {"success": True}), 200, {"ContentType": "application/json"}


def run_server():
    """Run server to render incoming statistics."""
    app.run(host=config.SERVER_HOSTNAME,
            port=config.SERVER_PORT,
            debug=config.SERVER_DEBUG, )


if __name__ == '__main__':
    run_server()
