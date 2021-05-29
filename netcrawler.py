import os
import sys
import re
import ipaddress
import netmiko
import csv
from netmiko import ConnectHandler

def convert_list_to_string(list_object, seperator=''):
    return seperator.join(list_object)

def read_switches():
    deviceList = []
    with open('./app/backend/device_list.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                device = {
                    "natip":convert_list_to_string(row[3]),
                    "internalip":convert_list_to_string(row[0]),
                    "portnumber": convert_list_to_string(row[4]),
                }
                deviceList += [device]
    return deviceList

def find_hostip(internalip, device_list):
    for d in device_list:
        if d["internalip"] == internalip:
            return (d["natip"], d["portnumber"])
    return 

def find_endpoint_location(endpoint_ip):
    ROUTER_IP = "10.101.1.205"
    END_DEVICE_IP = endpoint_ip

    MAC_REGEX = r'([0-9a-f]{4}[\.][0-9a-f]{4}[\.][0-9a-f]{4})'
    IP_REGEX = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    INTERFACE_REGEX = r'[A-Za-z]+[0-9]+[/]+[0-9]'

    PATH_TO_ENDPOINT = []
    PATH_TO_ENDPOINT += [{"endpoint_ip":END_DEVICE_IP}]

    ## ROUTER LOOP - FIND FIRST SWITCH

    #ssh to router 
    ROUTER_DEVICE = {
                'device_type': 'cisco_ios',
                'ip':   ROUTER_IP,
                'username': 'cisco',
                'password': 'cisco',
                'port' : 22,          # optional, defaults to 22
                'secret': 'cisco',     # optional, defaults to ''
            }
    switch_ip = ""
    try:
        router_connect = ConnectHandler(**ROUTER_DEVICE)
        print(f"-----------------------------------")
        print(f"Connected to router at {ROUTER_IP}")

        #ping ip of endpoint 
        ping_output = router_connect.send_command("ping " + END_DEVICE_IP)
        print(ping_output)

        #send command(sh ip arp "saved_ip")
        #save interface of "saved_ip" = "interface_to_endpoint" (exclude whatever is after ".")
        iparp_output = router_connect.send_command("sh ip arp " + END_DEVICE_IP)
        router_interface = re.findall(INTERFACE_REGEX, iparp_output)[0]
        print(f"Router interface found: {router_interface}")

        #send command (sh cdp nei "interface_to_endpoint" det)
        #save "management ip address"
        cdp_output = router_connect.send_command("sh cdp nei " + router_interface + " det")
        switch_ip_list = re.findall(IP_REGEX, cdp_output)
        switch_ip = convert_list_to_string(switch_ip_list[0],'')
        switch_int_list = re.findall(INTERFACE_REGEX, cdp_output)
        switch_int = convert_list_to_string(switch_int_list[1],'')

        PATH_TO_ENDPOINT += [{"ip": ROUTER_IP, "ininterface": "None", "outinterface": router_interface}]
        
        print(f"First switch IP found: {switch_ip}")
    except Exception as exc:
        print(f"ERROR OCCURED: {exc.args}")
        PATH_TO_ENDPOINT = [{"errormessage": "Some issues at router " + ROUTER_IP, "endpoint_ip":END_DEVICE_IP}]
        return PATH_TO_ENDPOINT

    ## SWITCH LOOP
    device_list = read_switches()
    while switch_ip:
        #ssh to router 
        conn = find_hostip(switch_ip, device_list)
        SWITCH_DEVICE = {
            'device_type': 'cisco_ios',
            'ip':  conn[0],
            'username': 'cisco',
            'password': 'cisco',
            'port' : conn[1],          # optional, defaults to 22
            'secret': 'cisco',     # optional, defaults to ''
        }
        try:
            switch_connect = ConnectHandler(**SWITCH_DEVICE)
            print(f"-----------------------------------")
            print(f"Connected to switch at {switch_ip}")

            #ping ip of endpoint 
            ping_output = switch_connect.send_command("ping " + END_DEVICE_IP)
            print(ping_output)

            #send command(sh ip arp "saved_ip")
            #save mac-address of "endpoint_mac"
            iparp_output = switch_connect.send_command("sh ip arp " + END_DEVICE_IP)
            mac_list = re.findall(MAC_REGEX, iparp_output)
            mac_next_switch = convert_list_to_string(mac_list[0],'')
            print(f"Switch MAC address found: {mac_next_switch}")

            #send command (sh mac address-table address "endpoint_mac")
            #save interface of "endpoint_mac" = "endpoint_interface"
            at_output = switch_connect.send_command("sh mac address-table address " + mac_next_switch)
            int_list = re.findall(INTERFACE_REGEX, at_output)
            int_next_switch = convert_list_to_string(int_list[0],'')
            print(f"Switch interface found: {int_next_switch}")

            #send command (sh cdp nei "interface_to_endpoint" det)
            #save "management ip address"
            cdp_output = switch_connect.send_command("sh cdp nei " + int_next_switch + " det")
            ip_list = re.findall(IP_REGEX, cdp_output)
            int_list = re.findall(INTERFACE_REGEX, cdp_output)
            
            if len(ip_list) != 0:
                #if cdp neig -> go to this switch and do the LOOP - FIND ENDPOINT
                out_int = convert_list_to_string(int_list[0],'')

                PATH_TO_ENDPOINT += [{"ip": switch_ip, "ininterface": switch_int, "outinterface": out_int}]

                switch_ip = convert_list_to_string(ip_list[0],'')
                switch_int = convert_list_to_string(int_list[1],'')
                print(f"Next switch IP found: {switch_ip}")
            else:
                #if empty -> this is the interface to the endpoint
                print(f"IP of switch to endpoint: {switch_ip}")
                print(f"Interface to endpoint: {int_next_switch}")

                PATH_TO_ENDPOINT += [{"ip": switch_ip, "ininterface": switch_int, "outinterface": int_next_switch}]

                switch_ip = ""
        except Exception as exc:
            print(f"ERROR OCCURED: {exc.args}")
            PATH_TO_ENDPOINT = [{"errormessage": "Some issues at switch " + switch_ip, "endpoint_ip":END_DEVICE_IP}]
            return PATH_TO_ENDPOINT
        
    return PATH_TO_ENDPOINT