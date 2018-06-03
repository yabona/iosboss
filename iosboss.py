
import sys
import csv
import configparser
import datetime 

from systemcfg import *
from routing import *
from vlan import *

config_file = []

# system_config sets up basic system parameters
def system_config(): 
    out = []
    out.append("\nhostname " + hostname)
    out.append("ip domain-name " + domain)
    if not domain_lookup:
        out.append("no ip domain lookup")
    return out

# auth_config configures VTY and CONS authentication schemes (including SSH)
def auth_config():
    out = []
    out.append("line vty 0 15\n  login local")
    if constrain_ssh==True:
        out.append("  transport input ssh")
    else:
        out.append("  transport input all")

    # Console config:
    out.append("line con 0")
    if cons_login==False:
        out.append("  no login")
    else:
        out.append("  login local")

    if logging_sync:
        out.append("  logging sync")
    if cons_timeout==False:
        out.append("  exec timeout 0 0")
    out.append("exit\n!")

    if password_encryption==True:
        out.append("service password encryption")
    out.append("banner login # " + banner_login + "#")
    out.append("username admin priv 15 secret " + admin_password)

    return out

# Configures services running on the device, and how they will be configured. 
def services_config():
    out = [] 
    if enable_ssh:
        out.append("crypto key generate rsa general-keys modulus " + rsa_modulus + "\n!")
        out.append("ip ssh version 2\nip ssh auth retries 5\nip ssh time-out 30")

    if http_server==True:
        out.append("ip http server")
    if http_server==False:
        out.append("no ip http server")    

    if https_server==True:
        out.append("ip http secure-server")
    if https_server==False:
        out.append("no ip http secure-server")

    if ipv6==True:
        out.append("ipv6 unicast-routing")
    
    if ip_routing==True:
        out.append("ip routing")

    out.append("!")
    return out

# VLAN database config:
def vlan_config():
    out = []

    out.append('\n! -- Vlan Database Config: \n')
    for i in vlan_db:
        vlan, name = str(i), vlan_db[i][0]
        out.append("vlan " + vlan)
        out.append("  name " + name)
        if vlan_db[i][1] == False:
            out.append("  state suspend")
    out.append("!\nexit\n!")
    
    return out 

# switch_config configures switchports according to the CSV file imported. 
def switch_config(): 
    out = []

    out.append('\n! -- Switch configuration: \n')

    with open('switch.csv', 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')

        for i in reader:
            out.append("interface " + i['interface'])
            out.append(
                "  description [" + i['port_id'] + "] :: " + i['comment'])
            if i['ac_vlan']:
                out.append(
                    "  switchport mode access\n  switchport access vlan " + i['ac_vlan'])
                out.append("  no shutdown\n!")
            elif i['tr_tag']:
                out.append(
                    "  switchport trunk encapsulation dot1q\n  switchport mode trunk")
                out.append(
                    "  switchport trunk native vlan " + i['tr_untag'])
                out.append(
                    "  switchport trunk allowed vlan " + i['tr_tag'])
                out.append("  no shutdown\n!")
            else:
                out.append("  switchport nonegotiate\n  shutdown\n!")
    out.append("exit\n!")
    return out

# svi_config configures switch virtual interfaces for inter-vlan routing.
def svi_config():
    out = []

    out.append('\n! -- SVI virtual interface configuration:\n')

    with open("svi.csv", 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')

        for i in reader:
            out.append("interface vlan " + i['vlan_id'])
            out.append("  description " + i['comment'])
            out.append("  ip address " + i['ipv4_addr'] + ' ' + i['ipv4_subn'])
            
            if not i['ipv6_local']:
                out.append("  ipv6 address autoconfig")
            else: 
                out.append("  ipv6 address " + i['ipv6_local'] + ' link-local')
            out.append("  ipv6 address " + i['ipv6_global'])


            if i['hsrp_ipv4']:
                out.append("  standby " + i['vlan_id'] + " ip " + i['hsrp_ipv4'])
                if i['hsrp_primary']:
                    out.append("  standby " + i['vlan_id'] + " priority 50")
                    out.append("  standby " + i['vlan_id'] + " preempt")
                else: 
                    out.append("  standby " + i['vlan_id'] + "priority 150")
            if i['dhcp_relay']:
                out.append("  ip helper address " + i['dhcp_relay'])
            out.append("  no shutdown\n!")
    out.append('exit\n!')
    return out

# routing_config defines how to handle IP and IPv6 routing protocols.
# Currently supported: EIGRP4, EIGRP6, OSPF4, RIPv2
def routing_config(): 
    out = []

    out.append('\n! -- Dynamic Routing Configuration:\n')

    for i in static_routes:
        out.append('ip route ' + i)
    out.append('!')

    if eigrp4_enable==True: 
        out.append('router eigrp ' + hostname.upper())
        out.append('  address-family ipv4 unicast autonomus-system ' + str(eigrp4_asn) +
            '\n    eigrp router-id ' + eigrp4_rid
        )
        
        for i in eigrp4_networks:
            out.append('    network ' + i)

        out.append('    af-interface default' +
            '\n      passive-interface' +
            '\n      exit-af-interface'
        )

        for i in eigrp4_interfaces:
            out.append('    af-interface ' + i + 
                '\n      no passive interface' +
                '\n      exit-af-interface'
            )
        if eigrp4_redist_static==True:
            out.append('    topology base' +
                '\n      redistribute static' + 
                '\n      exit'
            )
        out.append('    exit-address-family\n  exit\n!')
        
    if eigrp6_enable==True:
        out.append('router eigrp ' + hostname.upper())
        out.append('  address-family ipv6 unicast autonomus-system ' + str(eigrp6_asn) +
            '\n    eigrp router-id ' + eigrp6_rid
        )

        out.append('    af-interface default' +
            '\n      passive-interface' +
            '\n      exit-af-interface'
        )

        for i in eigrp6_interfaces:
            out.append('    af-interface ' + i + 
                '\n      no passive interface' +
                '\n      exit-af-interface'
            )
        if eigrp6_redist_static==True:
            out.append('    topology base' +
                '\n      redistribute static' + 
                '\n      exit'
            )
        out.append('    exit-address-family\n  exit\n!')

    if ospf4_enable==True:
        out.append('router ospf 1' +
            '\n  router-id ' + ospf4_rid
        )
        for i in ospf4_networks:
            out.append('  network ' + i + ' area ' + str(ospf4_networks[i]))
        out.append('exit\n!')
    return out

# Main function, outputs the results to a file and/or the console. 
def main(): 

    config_file = []
    config_file.append([
        '! -- Configuration script for device' + hostname, 
        '! -- Generated on ' + datetime.datetime.now().isoformat(),
        '! -- https://github.com/yabona/iosboss\n\n',
        'configure terminal'
    ])
    # Comment out the functions of the device not being configured: 
    config_file.append(system_config())
    config_file.append(auth_config())
    config_file.append(services_config())
    config_file.append(vlan_config())
    config_file.append(switch_config())
    config_file.append(svi_config())
    config_file.append(routing_config())

    config_file.append(['do write-memory'])

    output_file_name = hostname + '.cfg'
    with open (output_file_name, 'a') as output:
        for i in config_file: output.write("\n".join(i))
    

main()
