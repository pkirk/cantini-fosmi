import hashlib
import requests
import uuid
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

login = os.getenv('LOGIN')  # Fetch login from environment variables
password = os.getenv('PASSWORD')  # Fetch password from environment variables

if not login or not password:
    raise ValueError("LOGIN and PASSWORD must be set in the environment variables")

hashed_password = hashlib.sha256(password.encode()).hexdigest()

# Define constants for VMC speeds
VMC_OFF = 0
VMC_SLEEP = 1
VMC_SPEED_1 = 2
VMC_SPEED_2 = 3
VMC_SPEED_3 = 4
VMC_AUTO = 16

# Tuple representing the VMC speeds, inutile :D
VMC_SPEEDS = (VMC_OFF, VMC_SLEEP, VMC_SPEED_1, VMC_SPEED_2, VMC_SPEED_3, VMC_AUTO)

PLATFORM_NAME = 'IntelliClima Homebridge';

PLUGIN_NAME = 'homebridge-intelliclima';

FCIC_CONFIG_API_FOLDER_MONO = '/server_v1_mono/api/';
FCIC_CONFIG_API_FOLDER_MULTI = '/server_v1_multi/api/';

FCIC_CONFIG_SERVER_HTTP = 'https://intelliclima.fantinicosmi.it';

def save_tokens(auth_token, token_id):
    with open('tokens.json', 'w') as f:
        json.dump({'auth_token': auth_token, 'token_id': token_id, 'timestamp': time.time()}, f)

def load_tokens():
    if os.path.exists('tokens.json'):
        with open('tokens.json', 'r') as f:
            data = json.load(f)
            if time.time() - data['timestamp'] < 86400:  # 1 day in seconds
                return data['auth_token'], data['token_id']
    return None, None

def eco_crc(buffer: str) -> str:
    """
    Computes the CRC-8 checksum using polynomial 0x31.

    :param buffer: Hexadecimal string (without spaces)
    :return: 2-character uppercase hexadecimal CRC checksum
    """
    buf = [int(buffer[i:i+2], 16) for i in range(0, len(buffer), 2)]

    crc = 0xFF  # Initial CRC value
    polynom = 0x31  # Polynomial used in the CRC calculation

    for byte in buf:
        crc ^= byte  # XOR with byte

        for _ in range(8):  # Process each bit
            if crc & 0x80:  # If MSB is set
                crc = ((crc << 1) ^ polynom) & 0xFF
            else:
                crc = (crc << 1) & 0xFF

    return f"{crc:02X}"  # Return as uppercase hex string

def create_speed_trama(device_serial: str, speed: int) -> str:
    """
    Creates a valid speed control trama for the device.

    :param device_serial: The hexadecimal device serial (8 characters)
    :param speed: Speed value (1, 2, or 3)
    :return: Complete trama including CRC
    """
    start_byte = "0A"
    command_type = "000E"
    function_code = "2F00"
    payload = f"50000004{speed:02X}"  # Adjust payload for speed
    buffer = device_serial + command_type + function_code + payload

    crc = eco_crc(buffer)  # Compute CRC checksum
    end_byte = "0D"

    trama = f"{start_byte}{buffer}{crc}{end_byte}"
    return trama

def send_command_to_device(auth_token, token_id, device_serial: str, speed: int):
    print(f'Sending command to device {device_serial}: {speed}')
    """
    Sends the generated speed command to the device via HTTP request.

    :param server_ip: The IP address of the server handling commands
    :param device_serial: The hexadecimal serial of the target device
    :param speed: The speed level (1, 2, or 3)
    """
    trama = create_speed_trama(device_serial, speed)
    url = f"{FCIC_CONFIG_SERVER_HTTP}/{FCIC_CONFIG_API_FOLDER_MONO}/eco/send/"
    headers = {
        'Tokenid': token_id,
        'Token': auth_token,
    }
    data = {"trama": trama}

    print(f"Sending command: {trama} to {url}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending command: {e}")

def login_and_get_tokens():
    login_url = f'{FCIC_CONFIG_SERVER_HTTP}/server_v1_mono/api/user/login/{login}/{hashed_password}'
    login_body = {
        'manufacturer': 'HomeAssistant',
        'model': 'Python',
        'platform': 'IntelliClimaHomeAssistant',
        'version': '0.0.1',
        'serial': 'unknown',
        'uuid': str(uuid.uuid4()).upper(),
        'language': 'english',
    }
    login_response = requests.post(login_url, json=login_body)
    login_response_json = json.loads(login_response.text)

    if login_response.status_code == 200 and login_response_json["status"] == 'OK':
        print('Login successful')
        auth_token = login_response_json["token"]
        token_id = login_response_json["id"]
        save_tokens(auth_token, token_id)
        return auth_token, token_id
    else:
        print('Login failed')
        print('Response:', login_response.text)
        exit()

class Device:
    def __init__(self, id, is_master, device_type, house_id, serial):
        self.id = id
        self.is_master = is_master
        self.type = device_type
        self.house_id = house_id
        self.serial = serial

class House:
    def __init__(self, id, name, devices):
        self.id = id
        self.name = name
        self.devices = devices

def save_houses(houses):
    houses_data = [
        {
            'id': house.id,
            'name': house.name,
            'devices': [
                {
                    'id': device.id,
                    'is_master': device.is_master,
                    'type': device.type,
                    'house_id': device.house_id
                } for device in house.devices
            ]
        } for house in houses
    ]
    with open('houses.json', 'w') as f:
        json.dump(houses_data, f, indent=2)

def get_houses(auth_token, token_id):
    elenco_url = f'{FCIC_CONFIG_SERVER_HTTP}/server_v1_mono/api/casa/elenco2/{token_id}'
    headers = {
        'Tokenid': token_id,
        'Token': auth_token,
    }

    elenco_response = requests.post(elenco_url, headers=headers)
    elenco_response_json = json.loads(elenco_response.text)

    if elenco_response.status_code == 200 and elenco_response_json["status"] == 'OK':
        print('Request to elenco2 successful')
        print('Response:', elenco_response.text)
        houses = []
        for house_id, devices in elenco_response_json["houses"].items():
            house_id = int(house_id)
            house_name = next((device["name"] for device in devices if device["id"] == -1), "Unknown")
            house_devices = [
                Device(
                    id=int(device["id"]),
                    is_master=device["isMaster"],
                    device_type=device["tipo"],
                    house_id=house_id
                ) for device in devices if device["id"] != -1
            ]
            houses.append(House(id=house_id, name=house_name, devices=tuple(house_devices)))
        save_houses(houses)
        return tuple(houses)
    else:
        print('Request to elenco2 failed')
        print('Response:', elenco_response.text)
        exit()

def get_device(auth_token, token_id, device_id):
    api_url = f'{FCIC_CONFIG_SERVER_HTTP}/server_v1_mono/api/sync/cronos380'
    # api_url = f'https://intelliclima.fantinicosmi.it/server_v1_mono/api/sync/ecocomforts'
    #headers = {
    #    'Tokenid': token_id,
    #    'Token': auth_token,
    #}
    body = {
        # "IDs": device_id,
        # "ECOs": "",
        "IDs": "",
        "ECOs": device_id,
        "includi_eco": True,
        "includi_ledot": True,
    }
    response = requests.post(api_url, json=body)
    response_json = json.loads(response.text)
    if response.status_code == 200 and response_json["status"] == 'OK':
        print('Request to cronos380 successful')
        print('Response:', response.text)
        return response_json
    else:
        print('Request to cronos380 failed')
        print('Response:', response.text)
        exit()

def load_houses():
    print('Loading houses')
    if os.path.exists('houses.json'):
        with open('houses.json', 'r') as f:
            houses_data = json.load(f)
            houses = []
            for house_data in houses_data:
                devices = [
                    Device(
                        id=device_data['id'],
                        is_master=device_data['is_master'],
                        device_type=device_data['type'],
                        house_id=device_data['house_id'],
                        serial=device_data['serial']
                    ) for device_data in house_data['devices']
                ]
                houses.append(House(id=house_data['id'], name=house_data['name'], devices=tuple(devices)))
            return houses
    print(f'No houses.json found')
    return []

def update_devices_info(auth_token, token_id, devices):
    device_ids = [str(device.id) for device in devices]
    response_json = get_device(auth_token, token_id, ", ".join(device_ids))
    if response_json and "data" in response_json:
        for device_info in response_json["data"]:
            device_id = int(device_info["id"])
            device_serial = device_info.get("crono_sn", "").upper()
            device_name = device_info.get("name", "")
            for device in devices:
                if device.id == device_id:
                    device.serial = device_serial
                    device.name = device_name

def save_houses_with_device_info(houses):
    houses_data = [
        {
            'id': house.id,
            'name': house.name,
            'devices': [
                {
                    'id': device.id,
                    'is_master': device.is_master,
                    'type': device.type,
                    'house_id': device.house_id,
                    'serial': getattr(device, 'serial', ''),
                    'name': getattr(device, 'name', '')
                } for device in house.devices
            ]
        } for house in houses
    ]
    with open('houses.json', 'w') as f:
        json.dump(houses_data, f, indent=2)

def get_all_devices(auth_token, token_id):
    houses = load_houses()
    all_devices = [device for house in houses for device in house.devices]
    update_devices_info(auth_token, token_id, all_devices)
    save_houses_with_device_info(houses)

def send_command_to_all_devices(auth_token, token_id, speed):
    print(f'Sending command to all devices: {speed}')
    houses = load_houses()
    for house in houses:
        print(f'House: {house.name}')
        for device in house.devices:
            print(f'Device: {device.id}, {device.type}, {device.serial}')
            if hasattr(device, 'serial') and device.serial:
                send_command_to_device(auth_token, token_id, device.serial, speed)
            else:
                print('Device serial not found')

auth_token, token_id = load_tokens()

if not auth_token or not token_id:
    print('No tokens found, logging in')
    auth_token, token_id = login_and_get_tokens()

#houses = get_houses(auth_token, token_id)
#for house in houses:
#    print(f'House ID: {house.id}, Name: {house.name}, Devices: {[(device.id, device.type) for device in house.devices]}')

# get_all_devices(auth_token, token_id)

# send_command_to_all_devices(auth_token, token_id, VMC_OFF)

get_device(auth_token, token_id, "31377")

# Devo fare una bella libreria.