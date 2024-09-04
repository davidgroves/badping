The file `example.pcap` was made by bringing up the vagrant environment, with a Linux KVM host, and running the following commands on boxA.

```sh
# Start the two VM's.
kvmhost$ vagrant up

# Connect to the VM's.  
kvmhost$ vagrant ssh boxA

### Send a normal ping
vagrant@boxA:/vagrant/badping$ ping -c 1 192.168.50.11
PING 192.168.50.11 (192.168.50.11) 56(84) bytes of data.
64 bytes from 192.168.50.11: icmp_seq=1 ttl=64 time=0.311 ms

--- 192.168.50.11 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.311/0.311/0.311/0.000 ms

### Send a ping with a bad FCS (note, this still gets a reply)
vagrant@boxA:/vagrant/badping$ sudo python3 badping.py --dst-mac 00:00:00:bb:bb:bb --dst-ipv4 192.168.50.11 --interface eth1 --frame-error 1 --count 1

### Send a ping with a bad FCS and a IPv4 checksum (no reply)
vagrant@boxA:/vagrant/badping$ sudo python3 badping.py --dst-mac 00:00:00:bb:bb:bb --dst-ipv4 192168.50.11 --interface eth1 --frame-error 1 --ip-error 1 --count 1

### Send a ping with a bad FCS, a bad IPv4 checksum, and a bad ICMP Echo Request checksum (no reply)
vagrant@boxA:/vagrant/badping$ sudo python3 badping.py --dst-mac 00:00:00:bb:bb:bb --dst-ipv4 192168.50.11 --interface eth1 --frame-error 1 --ip-error 1 --icmp-error 1 --count 1
```