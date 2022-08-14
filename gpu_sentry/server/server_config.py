# Server-side configuration.
PERMIT_CLIENTS = {
    # FULL_HOSTNAME is obtained by socket.gethostname()
    "FULL_HOSTNAME": {
        "codename": "KNOWN_AS_NAME",
        "name": "(SYSTEM_NAME)",
    },
}

SERVER_DEBUG = False
SERVER_HOSTNAME = "abc.xyz"
SERVER_PORT = 8000
