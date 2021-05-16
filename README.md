# Jamulus python library

The library supports sending and receiving of [Jamulus](https://github.com/jamulussoftware/jamulus/) protocol messages.

## Usage example

* Fetch server list from central (directory) server

```python
import jamulus

server = ("<hostname>", jamulus.DEFAULT_PORT)

jc = jamulus.JamulusConnector()
jc.sendto(server, "CLM_REQ_SERVER_LIST")

try:
    while True:
        addr, key, count, values = jc.recvfrom(timeout=1)
        if key == "CLM_SERVER_LIST":
            for server in values:
                print(f'{server["name"]} ({server["max_clients"]})')
except TimeoutError:
    pass
```

## Scripts

### `central_server.py`

* Simple implementation of a _Jamulus Central Server_
* _Jamulus Servers_ can register / unregister
* _Jamulus Clients_ can get list of registered servers

### `central_proxy.py`

* Collect server lists from multiple _Jamulus Central Servers_
* Filters servers by their country ID
* _Jamulus Clients_ can get filtered list of servers

### `dummy_server.py`

* Simulates a _Jamulus Server_

### `dummy_client.py`

* Simulates a _Jamulus Client_ connecting to a _Jamulus Server_

## Limitations

* The implementation is not proven / tested to be 100% reliable
* Certain exceptions are not handled and can crash the process

## References

These projects were very helpful to understand the Jamulus protocol:
- [softins/jamulus-php](https://github.com/softins/jamulus-php)
- [softins/jamulus-wireshark](https://github.com/softins/jamulus-wireshark)
