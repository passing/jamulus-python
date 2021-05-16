#!/usr/bin/python3

import jamulus

import argparse
import signal
import sys


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=jamulus.DEFAULT_PORT, help="local port number")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="print protocol data",
    )
    return parser.parse_args()


def main():
    # get arguments
    args = argument_parser()

    # create jamulus connector
    jc = jamulus.JamulusConnector(port=args.port, debug=args.debug)

    # create empty server list
    server_list = {}

    # receive messages indefinitely
    while True:
        addr, key, count, values = jc.recvfrom()

        if key == "AUDIO":
            # stop clients from connecting
            jc.sendto(addr, "CLM_DISCONNECTION")

        elif key in ["CLM_REGISTER_SERVER", "CLM_REGISTER_SERVER_EX"]:
            # add server to list
            values["ip"] = addr[0]
            server_list[addr] = values

            print("registering server\n{}".format(values))

            # send successful registration response
            jc.sendto(addr, "CLM_REGISTER_SERVER_RESP", {"status": 0})

        elif key == "CLM_UNREGISTER_SERVER":
            print("unregistering server")

            # remove server from list
            if addr in server_list.keys():
                del server_list[addr]

        elif key == "CLM_REQ_SERVER_LIST":
            # send server list with dummy entry in first position
            server_list_send = [
                {
                    "ip": "0.0.0.0",
                    "port": 0,
                    "country_id": 0,
                    "max_clients": 0,
                    "permanent": 0,
                    "name": "",
                    "internal_address": "",
                    "city": "",
                }
            ] + list(server_list.values())
            print("sending {} servers\n{}".format(len(server_list_send), server_list_send))
            jc.sendto(addr, "CLM_SERVER_LIST", server_list_send)


def signal_handler(sig, frame):
    print()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
