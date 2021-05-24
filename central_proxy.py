#!/usr/bin/python3

import jamulus

import argparse
import signal
import sys

from time import time


DEFAULT_INTERVAL = 300


class ServerList(dict):
    def format_server(server):
        age_seconds = int(time() - server["time_updated"]) if "time_updated" in server.keys() else "?"
        return "{:>15}:{:<5} {} {:<20} {:>3}/{:>3} {}/{} ({}/{}) {}s {}".format(
            server.get("ip", 0),
            server.get("port", 0),
            "*" if server.get("permanent", 0) == 1 else " ",
            server.get("name", "?"),
            server.get("clients", "?"),
            server.get("max_clients", "?"),
            server.get("city", "?"),
            jamulus.COUNTRY_KEYS.get(server.get("country_id"), "?"),
            jamulus.OS_KEYS.get(server.get("os"), "?"),
            server.get("version", "?"),
            age_seconds,
            server.get("internal_address", ""),
        )

    def __str__(self):
        return "\n".join(list(map(ServerList.format_server, self.values())))

    def update_server(self, key, values):
        if key in self.keys():
            self[key].update(values)
            self[key]["time_updated"] = time()

    def create_or_update_server(self, key, values):
        if key not in self.keys():
            self[key] = {"time_created": time()}
        self.update_server(key, values)

    def add_single(self, source_host, server):
        server["ip"] = source_host[0]
        key = (server["ip"], server["port"])
        self.create_or_update_server(key, server)
        print(ServerList.format_server(self[key]))

    def add_list(self, source_host, server_list):
        for server in server_list:
            if server["ip"] == "0.0.0.0":
                # central servers first (own) entry
                server["ip"], server["port"] = source_host
            server["source_host"] = source_host
            key = (server["ip"], server["port"])
            self.create_or_update_server(key, server)

    def remove_server(self, key):
        if key in self.keys():
            print(ServerList.format_server(self[key]))
            del self[key]

    def get_list(self, add_dummy=True):
        server_list = list(self.values())
        if add_dummy:
            server_list.insert(
                0,
                {
                    "ip": "0.0.0.0",
                    "port": 0,
                    "country_id": 0,
                    "max_clients": 0,
                    "permanent": 1,
                    "name": "Jamulus Proxy",
                    "internal_address": "",
                    "city": "",
                },
            )
        return server_list

    def filter(self, country_ids):
        if len(country_ids) > 0:
            filtered = dict((k, s) for k, s in super().items() if s["country_id"] in country_ids)
            super().clear()
            super().update(filtered)

    def copy(self):
        return ServerList(super().copy())


class ActionScheduler:
    def __init__(self, jamulus, central_servers, interval):
        self.jamulus = jamulus
        self.central_servers = central_servers
        self.interval = interval
        self.next_action = time()

    def run(self):
        # request server lists
        if self.next_action <= time():
            print("request server lists")

            for addr in self.central_servers:
                self.jamulus.sendto(addr, "CLM_REQ_SERVER_LIST")

            self.next_action += self.interval

        # return maximum time after which the scheduler needs to run again
        return self.next_action - time()


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=jamulus.DEFAULT_PORT, help="local port number")
    parser.add_argument(
        "--centralserver",
        type=jamulus.server_argument,
        required=True,
        action="extend",
        nargs="+",
        default=[],
        help="central servers for collecting server lists",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help="central server collection interval",
    )
    parser.add_argument(
        "--filter",
        type=int,
        action="extend",
        nargs="+",
        default=[],
        help="country IDs to filter",
    )
    parser.add_argument(
        "--log-data",
        action="store_true",
        help="log protocol data",
    )
    return parser.parse_args()


################################################################################


def main():
    # get arguments
    args = argument_parser()

    # create jamulus connector
    jc = jamulus.JamulusConnector(port=args.port, log_data=args.log_data)

    # create empty server list
    server_list = ServerList()

    # initiate repeated actions
    scheduler = ActionScheduler(
        jamulus=jc,
        central_servers=args.centralserver,
        interval=args.interval,
    )

    # receive messages indefinitely
    while True:
        timeout = scheduler.run()

        if timeout is not None and timeout <= 0:
            print("negative timeout {}".format(timeout))
            continue

        try:
            addr, key, count, values = jc.recvfrom(timeout)
        except TimeoutError:
            continue

        if key == "AUDIO":
            # stop clients from connecting
            jc.sendto(addr, "CLM_DISCONNECTION")

        elif key == "CLM_SERVER_LIST":
            # add servers to list
            print("add/update {} servers".format(len(values)))
            server_list.add_list(addr, values)

        elif key == "CLM_REQ_SERVER_LIST":
            # get and filter server list
            server_list_send = server_list.copy()
            server_list_send.filter(args.filter)

            # send (filtered) server list
            print("sending {} servers\n{}".format(len(server_list_send), server_list_send))
            jc.sendto(addr, "CLM_SERVER_LIST", server_list_send.get_list())


def signal_handler(sig, frame):
    print()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
