#!/usr/bin/env python2.7
import logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)-15s %(levelname)-8s %(name)-20s %(message)s'
)
#import tftpy
import StringIO
import argparse
import sys
import json
import zmq
import threading


class Reader(threading.Thread):
    def __init__(self, savedb_path):
        threading.Thread.__init__(self)
        self.daemon = True
        self.savedb_path = savedb_path
        self.db = {}
        try:
            with open(self.savedb_path) as fp:
                self.db = json.loads(fp.read().decode('ascii'))
        except IOError as ioe:
            pass
        self.db_lock = threading.Lock()

    def run(self):
        ctx = zmq.Context()
        skt = ctx.socket(zmq.PULL)
        skt.bind('ipc:///var/run/lis-cain.sock')
        while True:
            msg = skt.recv()
            data = json.loads(msg.decode('ascii'))
            self.db_lock.acquire()
            self.db[data['client_ip']] = data
            with open(self.savedb_path, 'w') as fp:
                fp.write(json.dumps(self.db))
            self.db_lock.release()
            logger.info('new data: %s', json.dumps(data))

    def get_by_ip(self, ip):
        ret = None
        self.db_lock.acquire()
        if ip in self.db:
            ret = self.db[ip]
        self.db_lock.release()
        return ret

logger = logging.getLogger('lis-cain')
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', required=True)
parser.add_argument('-s', '--savedb', required=True)
args = parser.parse_args()

r = Reader(args.savedb)
r.start()

config = None
with open(args.config) as fp:
    config = json.loads(fp.read())

replace_data = None

class ConfigException(Exception):
    pass

class ConfigFile(StringIO.StringIO):
    def close(self):
        logger.info("sent config to switch")
        return StringIO.StringIO.close(self)

def build_switch_info_dict(switch_config, config_dict):
    if '_include' not in switch_config:
        return switch_config
    if 'switchgroups' not in config_dict:
        logger.error('switchgroups key missing from config while switches have _include clause(s)')
        raise ConfigException()
    if switch_config['_include'] not in config_dict['switchgroups']:
        logger.error('target include key (%s) missing from config switchgroups', switch_config['_include'])
        raise ConfigException()
    ret = {}
    for key, value in config_dict['switchgroups'][switch_config['_include']].items():
        ret[key] = value
    for key, value in switch_config.items():
        if key != '_include':
            ret[key] = value
    return ret

def get_config(remote_info):
    if remote_info['switch'] not in config['mapping']:
        logger.error('switch %s not in configuration', remote_info['switch'])
        return StringIO.StringIO()
    switch = config['mapping'][remote_info['switch']]
    if remote_info['switch_port'] not in switch['maps']:
        logger.error('switchport %s: %s not in configuration maps', switch['name'], remote_info['switch_port'])
        return StringIO.StringIO()
    to_configure_switch_name = switch['maps'][remote_info['switch_port']]
    if to_configure_switch_name not in config['switches']:
        logger.error('switch %s does not have configuration information', to_configure_switch_name)
        return StringIO.StringIO()
    to_configure_switch_info = build_switch_info_dict(config['switches'][to_configure_switch_name], config)
    with open('%s/%s' % (config['template_directory'], to_configure_switch_info['template'])) as fp:
        logger.info("sending configuration to %s", to_configure_switch_name)
        content = fp.read()
        out_data = content % to_configure_switch_info
        out_data_encoded = out_data.encode('ascii', errors='ignore')
        return ConfigFile(out_data_encoded)
    return StringIO.StringIO()

def serve_file(name, **kwargs):
    remote_addr = kwargs['raddress']
    remote_info = r.get_by_ip(remote_addr)
    if remote_info is not None:
        try:
            return get_config(remote_info)
        except BaseException as be:
            logger.exception(be)
            return StringIO.StringIO()
    logger.warn("%s requested file: %s, returning empty file (no remote info)", remote_addr, name)
    return StringIO.StringIO()

srv = None
try:
    srv = tftpy.TftpServer(tftproot='/tftproot', dyn_file_func=serve_file)
    srv.listen()
except BaseException as be:
    logger.exception(be)
    raise
