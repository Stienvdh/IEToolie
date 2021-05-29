import os
import requests
import json
from flask import Flask, send_file, jsonify, request
import mac_sticky, threadedscript, netcrawler

def main():
    index_path = os.path.join(app.static_folder, "index.html")
    return send_file(index_path)

def hello():
    return jsonify({'greeting':'Hello from Flask!'})

def upload_file_function():
    uploaded_file = request.files
    file_dict = uploaded_file.to_dict()
    the_file = file_dict["file"]
    the_file.save("./app/backend/device_list.csv")
    mac_sticky.writeInitialResultsFile()
    return jsonify("File has been uploaded")

def mac_sticky_function():
    thread = threadedscript.RunScriptThread()
    thread.start()
    thread.join()
    return jsonify("Started script")

def cli_output_function():
    body = mac_sticky.returnCLIOutput()
    return jsonify(body)

def result_function():
    body = mac_sticky.returnResults()
    return jsonify(body)

def find_device():
    ip_address = request.get_json(force=True)["ip-address"]
    body = netcrawler.find_endpoint_location(ip_address)
    return jsonify(body)
