# { vlan_id: ("Description", [bool]Active, STP_priority)
vlan_db = {
    10: ("Finance-2Floor", True, "ROOT"),
    15: ("Marketing-3Floor", True, "ROOT"),
    20: ("Sales-4Floor", True, 8192),
    25: ("Research-5Floor", True, 8192),

    80: ("Inactive", False, 4096),
    99: ("Trunk", True, 4096),
    101: ("IT", True, 4096),
}

vtp_version = 3
vtp_mode = "Server",
vtp3_primary = True
vtp_domain = "SW-Lab"
vtp_password = "Cisco123"
vtp_pruning = True 
