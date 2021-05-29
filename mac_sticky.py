
##############################################
# Version: 1.8
# Author:  Sami Wehbi
# Github:  https://github.com/habalpy/Python/
##############################################

import os
import sys
import re
import csv
import time
import ipaddress
import netmiko
import json
from netmiko import ConnectHandler
from netmiko.ssh_exception import  NetMikoTimeoutException
from paramiko.ssh_exception import SSHException 
from netmiko.ssh_exception import  AuthenticationException
import time

add_static_mac = ["switchport port-security mac-address sticky "] 

cli_output = ""

def findMACAddress(str):
    cisco_mac_regex = "([a-fA-F0-9]{4}[\.]?)"
    p = re.compile(cisco_mac_regex)
    result = re.findall(p, str)
    result_joined = ''.join(result)
    add_static_mac.append(result_joined)
    return result_joined
    
def checkMACAddress(str):
    result = re.match(r"([a-fA-F0-9]{4}[\.]?)",str)
    if result == True:
        return(bool(result))
    else:
        return(bool(result))
       
def convert_list_to_string(list_object, seperator=''):
    return seperator.join(list_object)

def runSimpleScript():
    print("Started simple script")
    device = ConnectHandler(device_type='cisco_ios', ip="10.101.1.205", port="2222",username='cisco', password='cisco', secret='cisco')
    device.enable()
    output1 = device.send_command("show mac address-table interface GigabitEthernet0/2")
    check_mac_value = findMACAddress(output1)
    MACCHECK = checkMACAddress(check_mac_value)
    if MACCHECK == True:
        print(check_mac_value)
    print("Ended simple script")

def writeInitialResultsFile():
    f = open("./app/backend/clioutput.txt","w+")
    f.close()
    deviceList = []
    with open('./app/backend/device_list.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print ("SKIPPING FIRST ROW")
                line_count += 1
            else:
                device = {
                    "hostip":convert_list_to_string(row[3]),
                    "internalip":convert_list_to_string(row[0]),
                    "endpointip": convert_list_to_string(row[1]),
                    "svi": convert_list_to_string(row[2]),
                    "portnumber": convert_list_to_string(row[4]),
                    "interface": "GigEth0/2",
                    "macaddress": "",
                    "sticked": ""
                }
                deviceList += [device]
    resultFile = open("./app/backend/results.txt","w+")
    json.dump(deviceList,resultFile)
    resultFile.close()
    
def runScript():
    try:
        deviceList = {}
        with open("./app/backend/results.txt", "r+") as f:
            output = f.read()
            deviceList = json.loads(output)
        index = 0
        for element in deviceList:
                Timeouts= open("./app/backend/Connection time outs.txt", "a")
                Authfailure= open("./app/backend/Auth failures.txt", "a")
                SSHException= open("./app/backend/SSH Failure.txt", 'a')
                EOFError= open("./app/backend/EOFerrors.txt",'a')
                UnknownError= open("./app/backend/UnknownError.txt",'a')
                #
                config_portsec_commands = ["interface GigabitEthernet0/2", "switchport mode access", "switchport access vlan 11", "switchport port-security", "switchport port-security mac-address sticky"]
                add_static_mac = ["switchport port-security mac-address sticky "] 
                host = element["hostip"]
                end_device_ip = element["endpointip"]
                svi = element["svi"]
                portnumber = element["portnumber"]
             
                try:
                    print("Before SSH " + host + " " + portnumber)
                    device = ConnectHandler(device_type='cisco_ios', ip=host, port=int(portnumber),username='cisco', password='cisco', secret='cisco',fast_cli=False, conn_timeout = 10)
                    print("After SSH")
                    device.enable()
                    output1 = device.send_command("show mac address-table interface GigabitEthernet0/2")
                    print(output1)
                    print (host)
                    print ("##########\n")
                    check_mac_value = findMACAddress(output1)
                    MACCHECK = checkMACAddress(check_mac_value) 
                    if MACCHECK == True:
                        static_conf = ''.join(add_static_mac)
                        config_portsec_commands.append(static_conf)
                        outF = open("SwitchLog-" + host + ".txt", "a")
                        output2 = device.send_command("show run interface GigabitEthernet0/2",delay_factor =5)
                        # with open("./app/backend/clioutput.txt", "a+") as f:
                        #     f.write(output2)
                        #     f.write("\n\n")
                        #     f.close()
                        print(output2)
                        outF.write("Switch " + host + " Pre Port Config Change # \n")
                        outF.write("\n")
                        outF.write(output2)
                        outF.write("\n")
                        outF.write("################\n")
                        outF.write("################\n")
                        configdev = device.send_config_set(config_portsec_commands)
                        output3 = device.send_command("show run interface GigabitEthernet0/2")
                        with open("./app/backend/clioutput.txt", "a+") as f:
                            f.write(output3 + "\n")
                            f.close()
                        print(output3)
                        outF.write("Switch " + host + " After Port Config Change # \n")
                        outF.write("\n")
                        outF.write(output3)
                        outF.write("\n")
                        outF.write("################\n")
                        outF.write("################\n")
                        print (host + " Completed")
                        device.send_command("write memory\n", delay_factor =10)
                        device.disconnect()
                        operationLOG = open("OperationLog.txt", "a")
                        operationLOG.write("Switch " + host + " Completed \n")

                        element["macaddress"] = check_mac_value
                        element["sticked"] = "Success"
                        with open("./app/backend/results.txt", "w+") as f:
                            json.dump(deviceList,f)
                            f.close()
                        
                    elif MACCHECK == False:

                        print ("NULL MAC ADDRESS")
                        outF = open("SwitchLog-" + host + ".txt", "a")
                        output4 = device.send_command("show run interface GigabitEthernet0/2")
                        outF.write("\n")
                        outF.write(output4)
                        outF.write("\n")
                        outF.write("################\n")
                        outF.write("################\n")
                        remove_vlan_interface_commands = ["no interface vlan 11"]
                        config_vlan_interface_commands = ["interface vlan 11", "no shutdown"]
                        add_svi = ["ip address "," 255.255.255.0"]                
                        add_svi.insert(1,svi)
                        oneliner = ''.join(add_svi)
                        config_vlan_interface_commands.append(oneliner)
                        #print(add_svi)
                        #print(oneliner)
                        #print(config_vlan_interface_commands)
                        configdev = device.send_config_set(config_portsec_commands)
                        configdev2 = device.send_config_set(config_vlan_interface_commands)
                        time.sleep(2)
                        output5 = device.send_command("ping " + end_device_ip + " repeat 5")
                        configdev3 = device.send_config_set(remove_vlan_interface_commands)
                        output6 = device.send_command("show run interface GigabitEthernet0/2", delay_factor =5)
                        outF.write("Switch " + host + " After Port Config Change # \n")
                        outF.write("\n")
                        outF.write(output6)
                        outF.write("\n")
                        outF.write("################\n")
                        outF.write("################\n")
                        print(output5)
                        print(output6)
                        print (host + " Completed")
                        operationLOG = open("OperationLog.txt", "a")
                        operationLOG.write("Switch " + host + " Completed \n")
                        # device.send_command("write memory\n", delay_factor =10)
                        time.sleep(2)

                        output1 = device.send_command("show mac address-table interface GigabitEthernet0/2")
                        print(output1)
                        print (host)
                        print ("##########\n")
                        check_mac_value = findMACAddress(output1)
                        MACCHECK = checkMACAddress(check_mac_value) 

                        if MACCHECK == True:
                            element["macaddress"] = check_mac_value
                            element["sticked"] = "Success"
                            with open("./app/backend/results.txt", "w+") as f:
                                json.dump(deviceList,f)
                                f.close()
                        elif MACCHECK == False:
                            element["sticked"] = "Endpoint Not Reachable"
                            with open("./app/backend/results.txt", "w+") as f:
                                json.dump(deviceList,f)
                                f.close()
                        
                        device.disconnect()
                        
                    else:
                        print("NOTHING WAS DONE to host" + host)
                        element["sticked"] = "Nothing?"
                        with open("./app/backend/results.txt", "w+") as f:
                            json.dump(deviceList,f)
                            f.close()
                # except (AuthenticationException):
                #     print ('Authentication Failure: ' + host)
                #     Authfailure.write('\n' + host)
                #     continue 
                # except (NetMikoTimeoutException):
                #     print ('\n' + 'Timeout to device: ' + host)
                #     Timeouts.write('\n' + host)
                #     continue
                # except (SSHException):
                #     print ('SSH might not be enabled: ' + host)
                #     SSHException.write('\n' + host)
                #     continue 
                # except (EOFError):
                #     print ('\n' + 'End of attempting device: ' + host)
                #     EOFError.write('\n' + host)
                #     continue

                except Exception as unknown_error:
                    print ('Some other error: ' + str(unknown_error))
                    element["sticked"] = "Host Not Reachable"
                    with open("./app/backend/results.txt", "w+") as f:
                            json.dump(deviceList,f)
                            f.close()
    except Exception as error:
        print ("Broken by this error: \n" + str(error))
    return

def returnCLIOutput():
    with open("./app/backend/clioutput.txt", "r+") as f:
        output = f.read()
        f.close()
    return output

def returnResults():
    with open("./app/backend/results.txt", "r+") as f:
        output = f.read()
        f.close()
    return output

def test():
    time.sleep(100)
    return "Well done"