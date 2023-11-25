#!/usr/bin/env python3

import argparse
import os
import subprocess



parser = argparse.ArgumentParser(description="OpenVPN Docker setup")
parser.add_argument("-p", "--purpose", required=True, type=str, help="Purpose of the VPN, e.g. torrent. Used to create a recognizable name for the container and its data directory.")
parser.add_argument("-v", "--vpn-address", type=str, help="Address of the OpenVPN server, defaults to the first non-loopback IP address found.")
parser.add_argument("-d", "--dns-server", action="append", dest="dns_servers", help="Use multiple times to specify the DNS servers to be pushed to clients. Defaults to 9.9.9.9 if no DNS servers are specified.")
parser.add_argument("-s", "--subnet", default="10.0.0.0/24", type=str, help="Subnet to use for clients, defaults to 10.0.0.0/24.")
parser.add_argument("-r", "--route", default="10.0.0.0/24", type=str, help="Route to add to the server configuration, defaults to the value of the subnet argument. Only set this if you know what you're doing. Support for multiple routes not implemented.")
parser.add_argument("-u", "--udp-port", default=1194, type=int, help="UDP port for the OpenVPN server, defaults to 1194.")
parser.add_argument("-t", "--tcp-port", default=1194, type=int, help="TCP port for the OpenVPN server, defaults to 1194.")
parser.add_argument("-a", "--allow-tcp", action="store_true", help="Enables creating the TCP fallback OpenVPN server.")
parser.add_argument("-c", "--client", type=str, help="Name of the OpenVPN client to create.")
args = parser.parse_args()


# Initialize vars
container_name = f"openvpn-{args.purpose}"
container_data = os.path.realpath(f"./container-data/{args.purpose}")
configuration_path = f"./client-configurations/{args.purpose}"
if not args.dns_servers:
	args.dns_servers = ["9.9.9.9"]
dns_flags = " ".join([f"-n {server}" for server in args.dns_servers])
# The Docker image used supports static client configuration by hardcoding a route for their subnet. If no routes are
# specified, the image will append this route to the server configuration.
# Passing the -d flag to ovpn_genconfig will prevent it from adding the static IP route, but this variable is saved in
# the container data and subsequently loaded by ovpn_getclient, which causes it not to append "redirect-gateway def1"
# to client configurations. As a result, clients won't tunnel all traffic through the VPN.
# In order to avoid both of these scenarios, we manually pass the default route to ovpn_genconfig.
# The user shouldn't have to know about this. If they specify a custom subnet but no route, update the route argument.
if args.subnet != parser.get_default("subnet"):
	if args.route == parser.get_default("route"):
		args.route = args.subnet


# Create the container data directory if necessary
if not args.client:
	try:
		os.mkdir(container_data)
	except FileExistsError:
		print(f"Error: Directory {container_data} already exists. You might want to delete the container and its data directory.")
		exit(1)
	# Create the configuration path if it doesn't exist
	try:
		os.mkdir(configuration_path)
	except FileExistsError:
		pass
else:
	if not os.path.isdir(container_data):
		print(f"Error: Directory {container_data} does not exist. Create an OpenVPN container first.")
		exit(1)


# Generate client certificate and configuration
if args.client:
	# Generate a client certificate without a passphrase
	subprocess.run(f"docker run -v {container_data}:/etc/openvpn --rm -it kylemanna/openvpn easyrsa build-client-full {args.client} nopass", shell=True, check=True)
	# Retrieve the client configuration with embedded certificates
	client_configuration_path = f"{configuration_path}/{args.client}.ovpn"
	subprocess.run(f"docker run -v {container_data}:/etc/openvpn --rm kylemanna/openvpn ovpn_getclient {args.client} > {client_configuration_path}", shell=True, check=True)
	print(f"Generated client certificate and configuration: {client_configuration_path}")
	exit()


# Set server address if not specified
if not args.vpn_address:
        args.vpn_address = subprocess.check_output("hostname -I | cut -d ' ' -f 1", shell=True).decode().strip()
        print(f"Auto-detected your IP address as {args.vpn_address}. If this is incorrect, override the value with the --vpn-address option.\n")

# Initialize the $OVPN_DATA container that will hold the configuration files and certificates.
# The container will prompt for a passphrase to protect the private key used by the newly generated certificate authority.
subprocess.run(f"docker run -v {container_data}:/etc/openvpn --rm kylemanna/openvpn ovpn_genconfig -u udp://{args.vpn_address} -s {args.subnet} -r {args.route} {dns_flags}", shell=True, check=True)
subprocess.run(f"docker run -v {container_data}:/etc/openvpn --rm -it kylemanna/openvpn ovpn_initpki", shell=True, check=True)

# Start OpenVPN server process
subprocess.run(f"docker run -v {container_data}:/etc/openvpn -d -p {args.udp_port}:1194/udp --cap-add=NET_ADMIN --name {container_name} kylemanna/openvpn", shell=True, check=True)

# If allowed, enable connecting via TCP as well
if args.allow_tcp:
	subprocess.run(f"docker run -v {container_data}:/etc/openvpn --rm -d -p {args.tcp_port}:1194/tcp --cap-add=NET_ADMIN --name {container_name}_tcp kylemanna/openvpn ovpn_run --proto tcp", shell=True, check=True)

# Print notices
print(f"\n{'=' * 80}")
if args.udp_port != parser.get_default("udp_port"):
	print("Be sure to edit the port number in the client configuration!")
if args.allow_tcp:
	print("You will need to edit the client configuration if you wish to connect using TCP.")
