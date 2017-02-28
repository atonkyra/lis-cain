#!/usr/bin/env python
import zmq
import os
import sys
import json


def pad_mac(mac):
    items = mac.split(':')
    mac_parts = []
    for item in items:
        mac_parts.append(int(item, 16))
    mac_comp = []
    for part in mac_parts:
        mac_comp.append('%02x' % (part))
    ret = ':'.join(mac_comp)
    return ret

if len(sys.argv) != 4:
    sys.exit(1)
  

if os.fork():
    sys.exit()

ctx = zmq.Context()
skt = ctx.socket(zmq.PUSH)
skt.set(zmq.LINGER, 500)
skt.connect('ipc:///var/run/lis-cain.sock')
jsn = {'client_ip': sys.argv[1], 'switch': pad_mac(sys.argv[2]), 'switch_port': sys.argv[3]}
skt.send(json.dumps(jsn).encode('ascii'))
