#!/usr/bin/python3

import jamulus

import argparse
import signal
import sys


BASE_NETW_SIZE = 22


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=jamulus.DEFAULT_PORT, help="local port number")
    parser.add_argument("--channels", type=int, default=1, help="number of channels")
    parser.add_argument("--clients", type=int, default=0, help="number of clients")
    parser.add_argument(
        "--centralserver",
        type=jamulus.server_argument,
        help="central server to register on",
    )
    parser.add_argument(
        "--log-data",
        action="store_true",
        help="log protocol data",
    )
    parser.add_argument(
        "--log-audio",
        action="store_true",
        help="log audio messages",
    )

    return parser.parse_args()


def main():
    global args, clients, jc

    args = argument_parser()

    jc = jamulus.JamulusConnector(port=args.port, log_data=args.log_data, log_audio=args.log_audio)

    if args.centralserver:
        jc.sendto(
            args.centralserver,
            "CLM_REGISTER_SERVER",
            {
                "ip": "0.0.0.0",
                "port": jamulus.DEFAULT_PORT,
                "country_id": 0,
                "max_clients": args.channels,
                "permanent": 0,
                "name": "Test Server",
                "internal_address": "",
                "city": "",
            },
        )

    clients = {}
    for id in range(args.clients):
        addr = ("0.0.0.0", id)
        clients[addr] = {
            "id": id,
            "country": 0,
            "instrument": 0,
            "skill": 0,
            "zero": 0,
            "name": f"Test {id}",
            "city": "",
        }
    clients_pending = []

    while True:
        addr, key, count, values = jc.recvfrom()

        if key == "AUDIO":
            if addr not in clients_pending + list(clients.keys()):
                clients_pending.append(addr)
                jc.sendto(addr, "CLIENT_ID", {"id": len(clients)})
                jc.sendto(addr, "CONN_CLIENTS_LIST", clients.values())
                jc.sendto(addr, "REQ_SPLIT_MESS_SUPPORT")
                jc.sendto(addr, "REQ_NETW_TRANSPORT_PROPS")
                jc.sendto(addr, "REQ_JITT_BUF_SIZE")
                jc.sendto(addr, "REQ_CHANNEL_INFOS")
                jc.sendto(
                    addr,
                    "CHAT_TEXT",
                    {"string": "<b>Server Welcome Message:</b> This is a Test Server"},
                )

            audio_values = jamulus.silent_audio(len(values["data"]))
            jc.sendto(addr, "AUDIO", audio_values)

        elif key == "CHANNEL_INFOS":
            id = len(clients)
            clients[addr] = values
            clients[addr]["id"] = id
            clients[addr]["zero"] = 0
            jc.sendto(addr, "CONN_CLIENTS_LIST", clients.values())
            if addr in clients_pending:
                clients_pending.remove(addr)

        elif key == "CLM_DISCONNECTION":
            # remove client from list
            if addr in clients.keys():
                del clients[addr]

        elif key == "CLM_PING_MS":
            # respond to ping request
            jc.sendto(addr, "CLM_PING_MS", values)

        elif key == "CLM_PING_MS_WITHNUMCLIENTS":
            # respond to ping request with client number
            jc.sendto(addr, "CLM_PING_MS_WITHNUMCLIENTS", values)

        elif key == "CLM_SEND_EMPTY_MESSAGE":
            # send empty messages when requested
            jc.sendto((values["ip"], values["port"]), "CLM_EMPTY_MESSAGE")

        elif key == "CLM_REQ_VERSION_AND_OS":
            # respond to request to send version and os
            values_send = {"os": 2, "version": "python-test"}
            jc.sendto(addr, "CLM_VERSION_AND_OS", values_send)

        elif key == "CLM_REQ_CONN_CLIENTS_LIST":
            # respond to request to send connected clients list
            jc.sendto(addr, "CONN_CLIENTS_LIST", clients.values())


def signal_handler(sig, frame):
    print()
    for addr in clients.keys():
        if addr[0] != "0.0.0.0":
            jc.sendto(addr, "CLM_DISCONNECTION")
    if args.centralserver:
        jc.sendto(args.centralserver, "CLM_UNREGISTER_SERVER")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
