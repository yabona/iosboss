acl_ext = {
    
    'block_ssh_in': {
        'action': 'deny',
        'protocol': 'tcp',
        'port': 22,
        'src': 'any'
        'dest': 'host 10.123.45.224'
    }    
    
}
