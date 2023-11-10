from bleak import BleakScanner, BleakClient
from bleak import exc
from modelos import create_tables
from modelos import Configuration
from time import sleep
from peewee import DoesNotExist
import asyncio
import struct
from modelos import Configuration, Datos, Logs
import datetime


TAG = "[RASP]"

CHAR_CONFIG = "0xFF01"

print(TAG, "Creando tablas")
create_tables()


def unpack_msg(packet:bytes):
    print(struct.unpack('<H6BBBH', packet[:12]))
    id, mac1,mac2,mac3,mac4,mac5,mac6, transport_layer, id_protocol, length = struct.unpack('<H6BBBH', packet[:12])
    mac = f"{hex(mac1)[2:]}:{hex(mac2)[2:]}:{hex(mac3)[2:]}:{hex(mac4)[2:]}:{hex(mac5)[2:]}:{hex(mac6)[2:]}"
    print(mac)

    header = {
        'header_id': id,
        'header_mac': str(mac),
        'transport_layer': transport_layer,
        'id_protocol': id_protocol,
        'length': length,
        'id_device': mac[:2]
    }
    body_packet = packet[12:] # struct.unpack('<{}s'.format(length), packet[12:])[0].decode('utf-8')
    print("body bytes: ", body_packet)
    body = parse_body(body_packet, id_protocol)
    return dict(header, **body) # retorna los datos usados por la tabla Datos

def parse_body(body:bytes, id_protocol:int) -> dict:
    data = ['batt_level', 'timestamp', 'temp', 'press', 'hum', 'co', 'rms', 'amp_x', 'frec_x','amp_y', 'frec_y','amp_z', 'frec_z']
    d = {}
    if id_protocol == 0:
        parsed_data = struct.unpack('<B', body)
        # Estructura del protocolo 0
        # HEADERS + Batt_level
        pass
    elif id_protocol == 1:
        parsed_data = struct.unpack('<BL', body)
        # Estructura del protocolo 1
        # HEADERS + Batt_level + Timestamp 
        pass
    elif id_protocol == 2:
        print(len(body))
        parsed_data = struct.unpack('<BLBiBf', body)
        # Estructura del protocolo 1
        # HEADERS + Batt_level + Timestamp + Temp + Press + Hum +Co
        pass
    elif id_protocol == 3:
        parsed_data = struct.unpack('<BLBiBifffffff', body)
    
    l = len(parsed_data)
    for k in range(l):
        d[data[k]] = parsed_data[k]
    return d

def create_data_row(data:dict):
    Datos.create(**data)
    print("[SERVER] Creada fila de la tabla Datos:", data)

def create_log_row(self, id_device):
    timestamp = datetime.now()
    config = self.config.get()
    print(config)
    log = {
        'id_device': id_device,
        'transport_layer':config['transport_layer'],
        'id_protocol': config['id_protocol'],
        'timestamp': timestamp
    }
    print(log)
    Logs.create(**log)
    print("[SERVER] Creada fila de la tabla Logs:", log)

class Config:
    def __init__(self, transport_layer=0, id_protocol=0):
        self.transport_layer = transport_layer
        self.id_protocol = id_protocol
        self.config = Configuration()
        self.row = None
        try:
            self.row = self.config.get_by_id(1)
        except DoesNotExist:
            default_row = {"transport_layer": self.transport_layer, "id_protocol": self.id_protocol}
            self.config.create(**default_row)
            self.row = self.config.get_by_id(1)

    def get(self):
        self.row = self.config.get_by_id(1)
        return (self.row.transport_layer, self.row.id_protocol)
    
    def set(self, transport_layer, id_protocol):
        self.row.transport_layer = transport_layer
        self.row.id_protocol = id_protocol
        self.row.save()



async def discover(self):
    devices = await self.scanner.discover()
    return devices

async def connect(self, device_mac):
    self.client = BleakClient(device_mac)
    connected = await self.client.connect()
    return connected

async def char_read(self, char_uuid):
    if self.client == None: return
    return await self.client.read_gatt_char(char_uuid)

async def char_write(self, char_uuid, data):
    if self.client == None: return
    await self.client.write_gatt_char(char_uuid, data)


CHARACTERISTIC_UUID = "0000ff01-0000-1000-8000-00805F9B34FB" # Busquen este valor en el codigo de ejemplo de esp-idf 


async def manage_server(device, config):
    while True:
        try:
            async with BleakClient(device, timeout=50) as client:
                client.connect()
                print("addres???: ", client.address)
                while True:
                    actual_config = config.get()
                    print(TAG, "La configuración es", actual_config)
                    # se pasa la configuracion
                    actual_config = f"con{actual_config[0]}{actual_config[1]}"
                    await client.write_gatt_char(CHARACTERISTIC_UUID, actual_config.encode())

                    # recibe datos
                    res = await client.read_gatt_char(CHARACTERISTIC_UUID)
                    print(f"Se leyo: {res}")

                    unpacked = unpack_msg(res)
                    print("Unpacked: ", unpacked)
                    create_data_row(unpacked)

                   

                    if actual_config[0] != 0:
                        # le ponemos que se duerma igual?
                        client.disconnect()
                        break
                
        except Exception as e:
            print(e)



async def main():
    config = Config()

    ADDRESS = ["3c:61:05:65:47:22"]

    await asyncio.gather(manage_server(ADDRESS[0], config)) # ahora solo hay que poner el segundo aca mismo y funca uwu  (en teoria)     
        
            
        

if __name__ == "__main__":
    asyncio.run(main())
