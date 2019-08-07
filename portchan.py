#!/usr/bin/env python3

import os
import argparse
import json
import jinja2

# These are added to all port channels
DEFAULT_VLANS = [1]

if not os.path.isdir('output'):
    os.mkdir('output')

parser = argparse.ArgumentParser('portchan.py')
parser.add_argument('-p', '--prefix', required=True)
parser.add_argument('-f', '--first', type=int, default=5)
parser.add_argument('-m', '--mode', default='desirable')
parser.add_argument('-d', '--distsw', default=[], action='append')

args = parser.parse_args()

prefix = args.prefix
first = args.first
mode = args.mode
distswlist = args.distsw

class Switch(object):
    def __init__(self, switch, vlans, ponum, mode, slaves):
        self.switch = switch
        self.vlans = vlans
        self.ponum = ponum
        self.mode = mode
        self.slaves = slaves

def gen_port(prefix, distport):
    module, portnum = distport.split('/')
    if not prefix[-1].isdigit():
        prefix += module
    port = '{}/{}'.format(prefix, portnum)

    return port

with open('config.json', 'r') as f:
    config = json.load(f)

for distsw in config['mapping'].values():
    distswname = distsw['name']
    if distswlist and not distswname in distswlist:
        continue

    ponum = first

    switchdict = {}
    for distport, accessw in distsw['maps'].items():
        if not accessw in switchdict.keys():
            switchdict[accessw] = [gen_port(prefix, distport)]
        else:
            switchdict[accessw].append(gen_port(prefix, distport))

    switches = []
    for switch, distports in switchdict.items():
        swconf = config['switches'][switch]
        if '_include' in swconf.keys():
            swgrp = config['switchgroups'][swconf['_include']]
            for option in swgrp:
                if not option in swconf.keys():
                    swconf[option] = swgrp[option]

        vlanlist = set()
        for vlan in DEFAULT_VLANS:
            vlanlist.add(vlan)
        vlanlist.add(swconf['mgmt_vlan'])
        vlanlist.add(swconf['visitor_access_vlan'])
        vlanlist = list(vlanlist)
        vlanlist.sort()

        vlans = ','.join(str(vlan) for vlan in vlanlist)
        switches.append(Switch(switch, vlans, ponum, mode, distports))

        ponum+=1

    with open('portchan.j2') as f:
        tmpl = jinja2.Template(f.read())
    rendered = tmpl.render(switches=switches)
    outfile = 'output/portchan-{}.txt'.format(distswname)
    with open(outfile, 'w') as f:
        f.write(rendered)
    print('Configuration written into file {}'.format(outfile))

    with open('cabling.j2') as f:
        tmpl = jinja2.Template(f.read())
    rendered = tmpl.render(name=distswname, switches=switchdict)
    outfile = 'output/cabling-{}.txt'.format(distswname)
    with open(outfile, 'w') as f:
        f.write(rendered)
    print('Cabling info written into file {}'.format(outfile))

