
import sys
import csv
import configparser
from systemcfg import *
from routing import *
from multilayer import *
from acl import *

config_file = []

# system config:
config_file.append("\nhostname " + hostname)
config_file.append("ip domain-name " + domain)

if not domain_lookup:
    config_file.append("no ip domain lookup")

# VTY session config:
config_file.append("line vty 0 15\n  login local")
if constrain_ssh==True:
    config_file.append("  transport input ssh")
else:
    config_file.append("  transport input all")

# Console config:
config_file.append("line con 0")
if cons_login==False:
    config_file.append("  no login")
else:
    config_file.append("  login local")
if logging_sync:
    config_file.append("  logging sync")
if cons_timeout==False:
    config_file.append("  exec timeout 0 0")
config_file.append("exit\n!")

if password_encryption==True:
    config_file.append("service password encryption")
config_file.append("banner login # " + banner_login + "#")
config_file.append("username admin priv 15 secret " + admin_password)

# Services config: 
if enable_ssh:
    config_file.append("crypto key generate rsa general-keys modulus " + rsa_modulus + "\n!")
    config_file.append("ip ssh version 2\nip ssh auth retries 5\nip ssh time-out 30")

if http_server==True:
    config_file.append("ip http server")
if http_server==False:
    config_file.append("no ip http server")    

if https_server==True:
    config_file.append("ip http secure-server")
if https_server==False:
    config_file.append("no ip http secure-server")

if ipv6==True:
    config_file.append("ipv6 unicast-routing")

# switch config (L2)
config_file.append("!")
with open('switch.csv') as csv_file:
    reader = csv.DictReader(csv_file, delimiter=',')

    for row in reader:
        config_file.append("interface " + row['interface'])
        config_file.append(
            "  description [" + row['port_id'] + "] :: " + row['comment'])
        if row['ac_vlan']:
            config_file.append(
                "  switchport mode access\n  switchport access vlan " + row['ac_vlan'])
            config_file.append("  no shutdown\n!")
        elif row['tr_tag']:
            config_file.append(
                "  switchport trunk encapsulation dot1q\n  switchport mode trunk")
            config_file.append(
                "  switchport trunk native vlan " + row['tr_untag'])
            config_file.append(
                "  switchport trunk allowed vlan " + row['tr_tag'])
            config_file.append("  no shutdown\n!")
        else:
            config_file.append("  switchport nonegotiate\n  shutdown\n!")

config_file.append("write memory\ny\n")

print("\n".join(config_file))
