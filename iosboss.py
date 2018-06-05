
import sys
import csv
import json
import configparser
import configparser
import datetime 

cfg = configparser.ConfigParser() 
cfg.read('config.ini')

config_file = []

# system_config sets up basic system parameters
def system_config(): 
    out = []
    out.append("\nhostname " + cfg.get('SYSTEM','hostname'))
    out.append("ip domain-name " + cfg.get('SYSTEM','domain'))

    if cfg.getboolean('SYSTEM','domain_lookup') == False:
        out.append("no ip domain lookup")
    return out

# auth_config configures VTY and CONS authentication schemes (including SSH)
def auth_config():
    out = []

    out.append('\n\n'+
        '! -------------------- !\n' +
        '! -- Authentication -- !\n' +
        '! -------------------- !\n'
    )

    out.append("line vty 0 15\n  login local")
    if cfg.getboolean('AUTH','constrain_ssh') == True:
        out.append("  transport input ssh")
    else:
        out.append("  transport input all")

    # Console config:
    out.append("line con 0")
    if cfg.getboolean('AUTH','cons_login') == False:
        out.append("  no login")
    else:
        out.append("  login local")
    if cfg.getboolean('AUTH','logging_sync') == True :
        out.append("  logging sync")
    if cfg.getboolean('AUTH','cons_timeout')==False:
        out.append("  exec timeout 0 0")
    out.append("exit\n!")

    # Password encryption: 
    if cfg.getboolean('AUTH','password_encryption') == True:
        out.append("service password encryption")

    out.append("banner login # " + cfg.get('AUTH','banner_login') + "#")
    out.append('username admin priv 15 secret ' + cfg.get('AUTH','admin_password'))
    out.append('\n')

    return out

# Configures services running on the device, and how they will be configured. 
def services_config():
    out = [] 

    out.append('\n' + 
        '! ---------------------------- !\n' +
        '! -- System services config -- !\n' +
        '! ---------------------------- !\n'
    )

    if cfg.getboolean('SERVICES','ssh_enable') == True:
        out.append("crypto key generate rsa general-keys modulus " + 
            cfg.get('SERVICES','rsa_modulus') + "\n!")
        out.append("ip ssh version 2\nip ssh auth retries 5\nip ssh time-out 30")

    if cfg.getboolean('SERVICES','http_server') == True:
        out.append("ip http server")
    if cfg.getboolean('SERVICES','http_server') == False:
        out.append("no ip http server")    

    if cfg.getboolean('SERVICES','https_server') == True:
        out.append("ip http secure-server")
    if cfg.getboolean('SERVICES','https_server') == False:
        out.append("no ip http secure-server")

    if cfg.getboolean('SERVICES','ipv6_routing') == True:
        out.append("ipv6 unicast-routing")
    
    if cfg.getboolean('SERVICES','ip_routing') == True:
        out.append("ip routing")

    return out

# VLAN database config:
def vlan_config():
    out = []

    out.append('\n\n' +
        '! -------------------------- !\n' +
        '! -- Vlan Database Config -- !\n' +
        '! -------------------------- !\n'
    )

    with open('vlan.csv', 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=',')

        for i in reader:
            out.append(
                "vlan " + i['vlan_id'] + "\n" +
                "  name "  + i['name'] + "\n" +
                "  state " + i['state'] 
            )
    out.append("  exit\n")
    return out 

# switch_config configures switchports according to the CSV file imported. 
def switch_config(): 
    out = []

    out.append('\n' +
        '! ----------------------- !\n' +
        '! -- Switchport Config -- !\n' +
        '! ----------------------- !\n'
    )

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
    out.append("exit\n")
    return out

# svi_config configures switch virtual interfaces for inter-vlan routing.
def svi_config():
    out = []

    out.append('\n' + 
        '! ------------------------- !\n' +
        '! -- Virtual Interfaces -- !\n' +
        '! ------------------------- !\n'
    )

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
    out.append('exit\n')
    return out

# Sets up routing information
def routing_config(): 
    out = []

    out.append('\n' + 
    '! ----------------------- !\n' +
    '! -- Routing Protocols -- !\n' +
    '! ----------------------- !\n')

    for i in json.loads(cfg.get('STATIC','static_routes')):
        out.append('ip route ' + i)
    out.append('!')
    return out 

# Configures the EIGRP routing protocol
def routing_config_eigrp():
    out = []

    # IPv4 EIGRP config: 
    if cfg.getboolean('EIGRP','eigrp4_enable')==True: 
        out.append('router eigrp ' + cfg.get('SYSTEM','hostname').upper())
        out.append('  address-family ipv4 unicast autonomous-system ' + cfg.get('EIGRP','eigrp4_asn') +
            '\n    eigrp router-id ' + cfg.get('EIGRP','eigrp4_rid')
        )
        
        for i in json.loads(cfg.get('EIGRP','eigrp4_networks')):
            out.append('    network ' + i)

        out.append('    af-interface default' +
            '\n      passive-interface' +
            '\n      exit-af-interface'
        )

        for i in json.loads(cfg.get('EIGRP','eigrp4_interfaces')):
            out.append('    af-interface ' + i + 
                '\n      no passive interface' +
                '\n      exit-af-interface'
            )
        if cfg.getboolean('EIGRP','eigrp4_redist_static')==True:
            out.append('    topology base' +
                '\n      redistribute static' + 
                '\n      exit'
            )
        out.append('    exit-address-family\n  exit\n!')
    
    # IPv6 EIGRP config: 
    if cfg.getboolean('EIGRP','eigrp6_enable')==True:
        out.append('router eigrp ' + cfg.get('SYSTEM','hostname').upper())
        out.append('  address-family ipv6 unicast autonomous-system ' + cfg.get('EIGRP','eigrp6_asn') +
            '\n    eigrp router-id ' + cfg.get('EIGRP','eigrp6_rid')
        )

        out.append('    af-interface default' +
            '\n      passive-interface' +
            '\n      exit-af-interface'
        )

        for i in json.loads(cfg.get('EIGRP','eigrp6_interfaces')):
            out.append('    af-interface ' + i + 
                '\n      no passive interface' +
                '\n      exit-af-interface'
            )
        if cfg.getboolean('EIGRP','eigrp6_redist_static') == True:
            out.append('    topology base' +
                '\n      redistribute static' + 
                '\n      exit'
            )
        out.append('    exit-address-family\n  exit\n!')
    return out 

# Configures the OSPF routing protocol
def routing_config_ospf(): 
    out = []
    out.append('\n')
    # OSPF config: 
    if cfg.getboolean('OSPF','ospf4_enable') == True:
        out.append('router ospf 1' +
            '\n  router-id ' + cfg.get('OSPF','ospf4_rid')
        )

        #areas = []
        for i in cfg.items('OSPF'):
            if 'area' in str(i):
                ar = i[0]
                ar_name = ar.replace('_', ' ')
                out.append('\n  ! -- ' + ar_name + ' enabled interfaces:')
                nets = json.loads(cfg.get('OSPF',ar))
                for n in nets:
                    out.append('  network ' + n + ' ' + ar_name) 
    out.append('  exit\n!\n')
    return out

# Main function, outputs the results to a file and/or the console. 
def main(): 

    config_file = []
    config_file.append([
        '! -- Configuration script for device ' + cfg.get('SYSTEM','hostname'), 
        '! -- Generated on {:%Y/%m/%d-%H:%M}'.format(datetime.datetime.now()),
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
    config_file.append(routing_config_eigrp())
    config_file.append(routing_config_ospf())
    
    config_file.append(['\ndo write-memory'])

    output_file_name = cfg.get('SYSTEM','hostname') + '{:-%Y%m%d-%H%M}.cfg'.format(datetime.datetime.now())
    with open (output_file_name, 'a') as output:
        for i in config_file: output.write("\n".join(i))
    

main()
