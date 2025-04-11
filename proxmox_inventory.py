#!/usr/bin/env python3

import json
import os
import sys
import argparse
import requests
import urllib3

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_proxmox_vms(hostname, username, password, verify_ssl=False):
    # Autenticación
    auth_url = f"https://{hostname}:8006/api2/json/access/ticket"
    auth_data = {"username": username, "password": password}
    
    try:
        auth_response = requests.post(auth_url, data=auth_data, verify=verify_ssl)
        auth_response.raise_for_status()
        
        ticket = auth_response.json()['data']['ticket']
        csrf_token = auth_response.json()['data']['CSRFPreventionToken']
        
        headers = {
            'Cookie': f'PVEAuthCookie={ticket}',
            'CSRFPreventionToken': csrf_token
        }
        
        # Obtener lista de nodos
        nodes_url = f"https://{hostname}:8006/api2/json/nodes"
        nodes_response = requests.get(nodes_url, headers=headers, verify=verify_ssl)
        nodes_response.raise_for_status()
        nodes = nodes_response.json()['data']
        
        inventory = {
            '_meta': {'hostvars': {}},
            'all': {'children': ['proxmox_vms']},
            'proxmox_vms': {'hosts': []},
            'proxmox_nodes': {'hosts': []},
            'running_vms': {'hosts': []},
            'stopped_vms': {'hosts': []}
        }
        
        # Añadir nodos Proxmox al inventario
        for node in nodes:
            node_name = node['node']
            inventory['proxmox_nodes']['hosts'].append(node_name)
            
            # Obtener VMs en este nodo
            vms_url = f"https://{hostname}:8006/api2/json/nodes/{node_name}/qemu"
            vms_response = requests.get(vms_url, headers=headers, verify=verify_ssl)
            vms_response.raise_for_status()
            vms = vms_response.json()['data']
            
            for vm in vms:
                vm_id = str(vm['vmid'])
                vm_name = vm['name']
                vm_status = vm['status']
                
                # Usar nombre de la VM como hostname
                inventory['proxmox_vms']['hosts'].append(vm_name)
                
                # Añadir a grupo según estado
                if vm_status == 'running':
                    inventory['running_vms']['hosts'].append(vm_name)
                else:
                    inventory['stopped_vms']['hosts'].append(vm_name)
                
                # Obtener configuración de la VM
                config_url = f"https://{hostname}:8006/api2/json/nodes/{node_name}/qemu/{vm_id}/config"
                config_response = requests.get(config_url, headers=headers, verify=verify_ssl)
                config_response.raise_for_status()
                config = config_response.json()['data']
                
                # Añadir variables específicas de la VM
                inventory['_meta']['hostvars'][vm_name] = {
                    'proxmox_node': node_name,
                    'proxmox_vmid': vm_id,
                    'proxmox_status': vm_status,
                    'proxmox_description': config.get('description', ''),
                    'proxmox_cores': config.get('cores', 1),
                    'proxmox_memory': config.get('memory', 512),
                    'ansible_host': vm_name  # Puedes personalizar esto según tu entorno
                }
        
        return inventory
        
    except Exception as e:
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Proxmox VM inventory script')
    parser.add_argument('--list', action='store_true', help='List all VMs')
    parser.add_argument('--host', help='Get info about specific host', default=None)
    args = parser.parse_args()
    
    # Leer variables de entorno
    proxmox_host = os.environ.get('PROXMOX_HOST', 'localhost')
    proxmox_user = os.environ.get('PROXMOX_USER', 'root@pam')
    proxmox_password = os.environ.get('PROXMOX_PASSWORD', '')
    verify_ssl = os.environ.get('PROXMOX_VERIFY_SSL', 'false').lower() == 'true'
    
    if args.list:
        inventory = get_proxmox_vms(proxmox_host, proxmox_user, proxmox_password, verify_ssl)
        print(json.dumps(inventory, indent=2))
    elif args.host:
        # Este script no implementa --host específicamente
        # pero podríamos extraerlo del inventario completo
        inventory = get_proxmox_vms(proxmox_host, proxmox_user, proxmox_password, verify_ssl)
        host_vars = inventory['_meta']['hostvars'].get(args.host, {})
        print(json.dumps(host_vars, indent=2))

if __name__ == '__main__':
    main()

