
static_routes = [
    '0.0.0.0 0.0.0.0 10.123.0.2'
]

# [EIGRP-IPv4]
eigrp4_enable = True
eigrp4_asn = 4200
eigrp4_rid = '1.1.1.4'
eigrp4_networks = ['0.0.0.0'] 
eigrp4_interfaces = ['vlan10','vlan15','vlan20','vlan25']
eigrp4_redist_static = True

# [EIGRP-IPv6]
eigrp6_enable = True
eigrp6_asn = 4200
eigrp6_rid = '1.1.1.6'
eigrp6_interfaces = ['vlan10','vlan15','vlan20','vlan25']
eigrp6_redist_static = True 

# [OSPF-IPv4]
ospf4_enable = True
ospf4_rid = '1.1.1.1'
ospf4_networks = {
    '10.123.10.2': 1,
    '10.123.15.2': 1,
    '10.123.20.2': 1,
    '10.123.25.2': 1,
    '10.123.1.0 0.0.0.3': 0

}

