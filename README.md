# openvpn-docker-setup

A utility for quickly deploying OpenVPN server instances in Docker using [kylemanna](https://github.com/kylemanna)'s [docker-openvpn](https://github.com/kylemanna/docker-openvpn) image.


## Deploying OpenVPN containers

Maybe you'd like a VPN for a seedbox running at home:

`./create.py --purpose torrent --udp-port 16384`

Or an always-active VPN to distance yourself from your ISP or cellular provider:

`./create.py --purpose general --udp-port 16384 --tcp-port 8443 --allow-tcp`

Or just a standard VPN on UDP port 1194:

`./create.py --purpose standard`


## Running multiple containers

Just change the port and client subnet for each container so that they don't conflict:

1. `./create.py --purpose primary --udp-port 1194 --subnet 10.0.0.0/24`
2. `./create.py --purpose secondary --udp-port 1195 --subnet 10.0.1.0/24`
3. `./create.py --purpose tertiary --udp-port 1196 --subnet 10.0.2.0/24`

You might also want to take at the OpenVPN wiki's [page on avoiding routing conflicts](https://community.openvpn.net/openvpn/wiki/AvoidRoutingConflicts).


## Generating client certificates and configurations

Simply run for each client you want to create.

`./create.py --purpose your-server-purpose --client your-client-name`


## Notes

The underlying Docker image is not forgiving of misspelled passphrases, so be careful to type them right the first time!


## Docker for noobs

List all containers:

`docker container list --all`

Delete a running container:

`docker rm --force openvpn-purpose`

See container statistics:

`docker stats --all`


## Usage

```
usage: create.py [-h] -p PURPOSE [-v VPN_ADDRESS] [-d DNS_SERVERS] [-s SUBNET] [-r ROUTE] [-u UDP_PORT] [-t TCP_PORT] [-a] [-c CLIENT]

OpenVPN Docker setup

options:
  -h, --help            show this help message and exit
  -p PURPOSE, --purpose PURPOSE
                        Purpose of the VPN, e.g. torrent. Used to create a recognizable name for the container and its data directory.
  -v VPN_ADDRESS, --vpn-address VPN_ADDRESS
                        Address of the OpenVPN server, defaults to the first non-loopback IP address found.
  -d DNS_SERVERS, --dns-server DNS_SERVERS
                        Use multiple times to specify the DNS servers to be pushed to clients. Defaults to 9.9.9.9 if no DNS servers are specified.
  -s SUBNET, --subnet SUBNET
                        Subnet to use for clients, defaults to 10.0.0.0/24.
  -r ROUTE, --route ROUTE
                        Route to add to the server configuration, defaults to the value of the subnet argument. Only set this if you know what you're doing. Support for multiple routes not implemented.
  -u UDP_PORT, --udp-port UDP_PORT
                        UDP port for the OpenVPN server, defaults to 1194.
  -t TCP_PORT, --tcp-port TCP_PORT
                        TCP port for the OpenVPN server, defaults to 1194.
  -a, --allow-tcp       Enables creating the TCP fallback OpenVPN server.
  -c CLIENT, --client CLIENT
                        Name of the OpenVPN client to create.
```
