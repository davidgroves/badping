# BadPing

## Purpose

To generate ping packets with three intentional errors.
 - Incorrect Ethernet Frame Checksum Sequence (FCS).
 - Incorrect IPv4 Checksum.
 - Incorrect ICMP Echo Request Checksum.

And to do so with "simple" Python code that you can "easily" read and understand.

## Prerequisites

- Python 3.10 or greater, and the packages in requirements.txt.
- You should run this in a Python virtual environment.
- Root privileges to create raw sockets.

## Vagrant Setup

Because setting up an exact environment for testing is difficult, a Vagrantfile is provided to set up two virtual machines (VMs) with the necessary configurations for the script to run. Some notes about the vagrant setup.

- It uses the Ethernet e1000 NIC's. It can't use libvirt's virtio NIC's, as they will not pass the required checksums.
- It sets up two VM's.

| Box  | Interface | MAC Address       | IP Address       | 
| ---- | --------- | ----------------- | ---------------- | 
| boxA | eth1      | 00:00:00:AA:AA:AA | 192.168.50.10/24 |
| boxB | eth1      | 00:00:00:BB:BB:BB | 192.168.50.11/24 |


```sh
vagrant up
```

This will create two VMs (boxA and boxB) with the necessary configurations for the script to run.

To connect to the VMs, run the following command:

```sh
vagrant ssh boxA
```

This will connect to the boxA VM.

## Usage

To get the support options, run badping with the `--help` flag:

```sh
cd /vagrant/badping/
python3 badping.py --help
```

```sh
cd /vagrant/badping
sudo python3 badping.py --src-mac AA:BB:CC:DD:EE:FF --dst-mac 00:11:22:33:44:55 --src-ipv4 192.168.50.10 --dst-ipv4 192.168.50.11 --interface eth1 --count 10 --delay 0.1 --ip-error 1
..........
```

Use `--frame-error 1` to have a 100% chance of a FCS error, `--ip-error 1` to have a 100% change of an IPv4 checksum error, and `--icmp-error 1` to have a 100% chance of an ICMP Echo Request checksum error.

## Debugging / Development

Note debugging / development is harder than I'd like. 

Running with `--icmp-error 1` will work. You will be able to do pcaps between the two VMs and see bad packets in `tcpdump -vvv` or `wireshark`. 

The other two are harder to test.
- No NIC supported by KVM will pass the FCS, even with `ethtool -K rx-fcs off; ethtool -K rx-all on; ethtool -K rx-checksumming off; ethtool -K tx-checksumming off`. So there is no way to test `--frame-error` on the virtual machines themselves.
- And libpcap won't capture packets with bad IPv4 checksums, so there is no way to test `--ip-error` on the virtual machines themselves either.
- However, you can attach `tcpdump` or `wireshark` to the `vnetX` interfaces on the KVM host, and therefore inspect the bad FCS frames and bad IPv4 checksum packets.

## Missing Features

- No IPv6 support. IPv6 doesn't have a layer3 checksum anyway, it expects the lower or higher layers to do it.

## Misc Notes

- The only thing Python is using a non-standard library package for is `netifaces`. If you remove the feature to detect the local MAC address, and make it a mandatory CLI argument, you could make this script run without any dependencies.
