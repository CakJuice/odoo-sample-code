# -*- coding: utf-8 -*-

import netifaces as ni


def get_ip():
    ip = ni.ifaddresses('eno2')[ni.AF_INET][0]['addr']
    return ip


def is_ip_server(ip_server='192.168.10.251'):
    ip = get_ip()
    return ip == ip_server
