#!/usr/bin/env python

import argparse
import struct
import socket
import sys
import os
import time
import zlib
import random
import netifaces
from typing import Optional

def mac_to_bytes(mac: str) -> bytes:
    return bytes(int(x, 16) for x in mac.split(':'))

def ipv4_to_bytes(ipv4: str) -> bytes:
    return socket.inet_aton(ipv4)

def get_mac_address(interface: str) -> str:
    try:
        mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
        return mac
    except KeyError:
        sys.stderr.write(f"Error: Could not get MAC address for interface {interface}\n")
        sys.exit(1)

def get_ip_address(interface: str) -> str:
    try:
        ipv4 = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
        return ipv4
    except KeyError:
        sys.stderr.write(f"Error: Could not get IP address for interface {interface}\n")
        sys.exit(1)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Generate a bad Ethernet frame with specified parameters.')
    parser.add_argument('--src-mac', help='Source MAC address (e.g., 01:02:03:04:05:06)')
    parser.add_argument('--dst-mac', required=True, help='Destination MAC address (e.g., 01:02:03:04:05:06)')
    parser.add_argument('--src-ipv4', help='Source IPv4 address (e.g., 192.168.1.1)')
    parser.add_argument('--dst-ipv4', required=True, help='Destination IPv4 address (e.g., 192.168.1.2)')
    parser.add_argument('--interface', required=True, help='Ethernet interface (e.g., eth0, eth1)')
    parser.add_argument('--delay', type=float, default=1.0, help='Interpacket delay in seconds (default: 1.0)')
    parser.add_argument('--count', type=int, default=4, help='How many packets to send (default: 4)')
    parser.add_argument('--frame-error', type=float, default=0.0, help='Percentage of frame checksum errors to introduce (default: 0.0)')
    parser.add_argument('--ip-error', type=float, default=0.0, help='Percentage of IP checksum errors to introduce (default: 0.0)')
    parser.add_argument('--icmp-error', type=float, default=0.0, help='Percentage of ICMP checksum errors to introduce (default: 0.0)')
    return parser.parse_args()

def check_if_root() -> None:
    if os.geteuid() != 0:
        sys.stderr.write("Error: This script must be run as root to use raw sockets.\n")
        sys.exit(1)

def calculate_icmp_checksum(data: bytes, error_prob: float) -> int:
    if len(data) % 2 == 1:
        data += b'\0'
    checksum: int = sum(struct.unpack('!%dH' % (len(data) // 2), data))
    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum += (checksum >> 16)
    checksum = ~checksum & 0xffff
    if random.random() < error_prob:
        checksum = random.randint(0, 0xFFFF)
    return checksum

def calculate_ip_checksum(data: bytes, error_prob: float) -> int:
    if len(data) % 2 == 1:
        data += b'\0'
    checksum: int = sum(struct.unpack('!%dH' % (len(data) // 2), data))
    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum += (checksum >> 16)
    checksum = ~checksum & 0xffff
    if random.random() < error_prob:
        checksum = random.randint(0, 0xFFFF)
    return checksum

def calculate_frame_checksum(data: bytes, error_prob: float) -> int:
    checksum = zlib.crc32(data) & 0xffffffff
    if random.random() < error_prob:
        checksum = random.randint(0, 0xFFFFFFFF)
    return checksum

def build_icmp_packet(packet_id: int, seq_number: int, error_prob: float) -> bytes:
    icmp_type: int = 8  # Echo request
    icmp_code: int = 0
    icmp_id: int = packet_id
    icmp_seq: int = seq_number
    icmp_payload: bytes = b'BadFrame' * 16  # Arbitrary payload
    icmp_header: bytes = struct.pack('!BBHHH', icmp_type, icmp_code, 0, icmp_id, icmp_seq)
    icmp_checksum: int = calculate_icmp_checksum(icmp_header + icmp_payload, error_prob)
    icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
    return icmp_header + icmp_payload

def build_ipv4_packet(src_ipv4: str, dst_ipv4: str, icmp_packet: bytes, error_prob: float) -> bytes:
    version_ihl: int = 0x45
    tos: int = 0
    total_length: int = 20 + len(icmp_packet)  # IPv4 header length + ICMP packet
    identification: int = random.randint(0, 0xFFFF)  # Random identification
    flags_fragment_offset: int = 0x4000  # Don't Fragment (DF) bit set
    ttl: int = 64
    protocol: int = socket.IPPROTO_ICMP
    header_checksum: int = 0

    src_ipv4_bytes: bytes = ipv4_to_bytes(src_ipv4)
    dst_ipv4_bytes: bytes = ipv4_to_bytes(dst_ipv4)

    ipv4_header: bytes = struct.pack(
        '!BBHHHBBH4s4s', version_ihl, tos, total_length, identification,
        flags_fragment_offset, ttl, protocol, header_checksum, src_ipv4_bytes, dst_ipv4_bytes
    )
    header_checksum = calculate_ip_checksum(ipv4_header, error_prob)
    ipv4_header = struct.pack(
        '!BBHHHBBH4s4s', version_ihl, tos, total_length, identification,
        flags_fragment_offset, ttl, protocol, header_checksum, src_ipv4_bytes, dst_ipv4_bytes
    )
    return ipv4_header + icmp_packet

def build_frame(src_mac: str, dst_mac: str, ipv4_packet: bytes, error_prob: float) -> bytes:
    src_mac_bytes: bytes = mac_to_bytes(src_mac)
    dst_mac_bytes: bytes = mac_to_bytes(dst_mac)
    ethertype: bytes = b'\x08\x00'  # Ethertype for IPv4
    frame: bytes = dst_mac_bytes + src_mac_bytes + ethertype + ipv4_packet
    fcs: bytes = struct.pack('!I', calculate_frame_checksum(frame, error_prob))
    return frame + fcs

def create_arp_request(own_mac: str, src_ip: str, target_ip: str) -> bytes:
    broadcast_mac = "ff:ff:ff:ff:ff:ff"
    ether_type = b'\x08\x06'  # ARP
    hw_type = b'\x00\x01'
    proto_type = b'\x08\x00'
    hw_size = b'\x06'
    proto_size = b'\x04'
    opcode = b'\x00\x01'  # request
    padding = b'\x00' * 18
    
    src_mac_bytes = mac_to_bytes(own_mac)
    broadcast_mac_bytes = mac_to_bytes(broadcast_mac)
    src_ip_bytes = ipv4_to_bytes(src_ip)
    target_ip_bytes = ipv4_to_bytes(target_ip)
    arp_frame = (
        broadcast_mac_bytes + src_mac_bytes + ether_type + hw_type +
        proto_type + hw_size + proto_size + opcode + src_mac_bytes + src_ip_bytes +
        mac_to_bytes("00:00:00:00:00:00") + target_ip_bytes + padding
    )
    return arp_frame

def main() -> None:
    args = parse_args()
    check_if_root()

    if not args.src_mac:
        args.src_mac = get_mac_address(args.interface)

    if not args.src_ipv4:
        args.src_ipv4 = get_ip_address(args.interface)

    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    s.bind((args.interface, 0))
    
    for seq_number in range(args.count):
        icmp_packet = build_icmp_packet(seq_number, seq_number, args.icmp_error)
        ipv4_packet = build_ipv4_packet(args.src_ipv4, args.dst_ipv4, icmp_packet, args.ip_error)
        frame = build_frame(args.src_mac, args.dst_mac, ipv4_packet, args.frame_error)
        s.send(frame)
        print(".", end="", flush=True)
        time.sleep(args.delay)

if __name__ == '__main__':
    main()
