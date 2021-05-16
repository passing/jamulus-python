#!/usr/bin/python3

import jamulus

import argparse
import signal
import sys


BASE_NETW_SIZE = 22
JITT_BUF_SIZE = 5


def argument_parser():
    def server_argument(string):
        server = string.split(":")
        if len(server) == 1:
            server.append(jamulus.DEFAULT_PORT)
        elif len(server) == 2:
            server[1] = int(server[1])
        else:
            raise ValueError
        return tuple(server)

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=jamulus.DEFAULT_PORT, help="local port number")
    parser.add_argument(
        "--server",
        type=server_argument,
        required=True,
        help="central server to register on",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="print protocol data",
    )
    parser.add_argument(
        "--hide-audio",
        action="store_true",
        help="do not log audio messages",
    )

    return parser.parse_args()


def main():
    global jc, args

    args = argument_parser()

    jc = jamulus.JamulusConnector(port=args.port, debug=args.debug, log_audio=not (args.hide_audio))

    audio_values = jamulus.silent_audio(BASE_NETW_SIZE)
    jc.sendto(args.server, "AUDIO", audio_values)

    audio_buffer = []

    while True:
        addr, key, count, values = jc.recvfrom()

        if key == "AUDIO":
            jc.sendto(addr, "AUDIO", audio_values)

        elif key == "REQ_SPLIT_MESS_SUPPORT":
            jc.sendto(addr, "SPLIT_MESS_SUPPORTED")
            pass

        elif key == "REQ_NETW_TRANSPORT_PROPS":
            jc.sendto(
                addr,
                "NETW_TRANSPORT_PROPS",
                {
                    "base_netw_size": BASE_NETW_SIZE,
                    "block_size_fact": 1,
                    "num_chan": 1,
                    "sam_rate": 48000,
                    "audiocod_type": 3,
                    "flags": 0,
                    "audiocod_arg": 0,
                },
            )

        elif key == "REQ_JITT_BUF_SIZE":
            jc.sendto(addr, "JITT_BUF_SIZE", {"blocks": JITT_BUF_SIZE})

        elif key == "REQ_CHANNEL_INFOS":
            jc.sendto(
                addr,
                "CHANNEL_INFOS",
                {
                    "country": 0,
                    "instrument": 0,
                    "skill": 0,
                    "name": "Test Client",
                    "city": "",
                },
            )


def signal_handler(sig, frame):
    print()
    jc.sendto(args.server, "CLM_DISCONNECTION")

    try:
        while True:
            jc.recvfrom(1)
    except TimeoutError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
