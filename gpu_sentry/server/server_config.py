# Server-side configuration.
PERMIT_CLIENTS = {
    # FULL_HOSTNAME is obtained by socket.gethostname()
    "FULL_HOSTNAME": {
        "codename": "KNOWN_AS_NAME",
        "name": "(SYSTEM_NAME)",
    },
    "gpu0": {
        "name": "gpu0.dqwang.online",
    },
    "gpu1": {
        "name": "gpu1.dqwang.online",
    },
    "gpu2": {
        "name": "gpu2.dqwang.online",
    },
}

SERVER_DEBUG = False
SERVER_HOSTNAME = "bj.dqwang.online"
SERVER_PORT = 8000
