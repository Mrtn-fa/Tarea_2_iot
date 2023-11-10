from bleak import BleakScanner, BleakClient
from bleak import exc
from modelos import create_tables
from modelos import Configuration
from time import sleep
from peewee import DoesNotExist
import asyncio
import struct
from modelos import Configuration, Datos, Logs, Loss
from datetime import datetime
from threading import Thread


TAG = "[RASP]"

CHAR_CONFIG = "0xFF01"

print(TAG, "Creando tablas")
create_tables()


def unpack_msg(packet:bytes):
    id, mac1,mac2,mac3,mac4,mac5,mac6, transport_layer, id_protocol, length = struct.unpack('<H6BBBH', packet[:12])
    mac = f"{hex(mac1)[2:]}:{hex(mac2)[2:]}:{hex(mac3)[2:]}:{hex(mac4)[2:]}:{hex(mac5)[2:]}:{hex(mac6)[2:]}"

    header = {
        'header_id': id,
        'header_mac': str(mac),
        'transport_layer': transport_layer,
        'id_protocol': id_protocol,
        'length': length,
        'id_device': mac[:5]
    }
    body_packet = packet[12:] # struct.unpack('<{}s'.format(length), packet[12:])[0].decode('utf-8')
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
        parsed_data = struct.unpack('<BLBiBf', body)
        # Estructura del protocolo 1
        # HEADERS + Batt_level + Timestamp + Temp + Press + Hum +Co
        pass
    elif id_protocol == 3:
        parsed_data = struct.unpack('<BLBiBffffffff', body)
    
    l = len(parsed_data)
    for k in range(l):
        d[data[k]] = parsed_data[k]
    return d

def create_data_row(data:dict):
    Datos.create(**data)
    print(TAG,"Creada fila de la tabla Datos:", data)

def create_log_row(config, id_device):
    timestamp = datetime.now()
    configs = config.get()
    log = {
        'id_device': id_device,
        'transport_layer':configs[0],
        'id_protocol': configs[1],
        'timestamp': timestamp
    }
    Logs.create(**log)
    print(TAG,"Creada fila de la tabla Logs:", log)
    return timestamp.timestamp()

def create_loss_row(delay, loss):
    loss = {
        'delay': delay,
        'packet_loss': loss
    }
    Loss.create(**loss)
    print(TAG,"Creada fila de la tabla Loss:", loss)

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
        print(TAG, "trying to connect to: ", device)
        try:
            async with BleakClient(device, timeout=5) as client:
                print(TAG, "Conected with: ", client.address)
                delta_time = 0
                
                while True:
                    actual_config = config.get()
                    print(TAG, "La configuración es", actual_config)

                    # se pasa la configuracion
                    send_config = f"con{actual_config[0]}{actual_config[1]}"
                    await client.write_gatt_char(CHARACTERISTIC_UUID, send_config.encode())
                    read_time = datetime.now().timestamp()

                    # recibe datos
                    res = await client.read_gatt_char(CHARACTERISTIC_UUID)

                    unpacked = unpack_msg(res)

                    if delta_time == 0 and actual_config[1] > 0:
                        delta_time = datetime.now().timestamp() - unpacked["timestamp"] # cuando se prendio
                    
                    if actual_config[1] > 0:
                        unpacked["timestamp"] = delta_time + unpacked["timestamp"] # cuando se prendio + segundos que pasaron desde que se prendio

                    # lo sube a la tabla
                    create_data_row(unpacked)
                    delay = (datetime.now().timestamp() - read_time) * 1000 # para pasar a mili segundos
                    loss = unpacked["length"] - len(res)
                    create_loss_row(delay, loss)

                    # sleep piola pa que no explote
                    await asyncio.sleep(1)

                    if actual_config[0] == 1:
                        print(TAG, "Disconnected with: ", client.address)
                        break

        except (exc.BleakDBusError, exc.BleakDeviceNotFoundError):
            await asyncio.sleep(5)

        except exc.BleakError as e:
            print(e)
                
        

def thread_target(loop, device, config):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(manage_server(device, config))

async def main():
    config = Config()

    ADDRESS = ["3c:61:05:65:47:22","ac:67:b2:3c:12:96"]
    # /dev/cu.usbserial-0001 izquierda
    # /dev/cu.usbserial-3 derecha
    connection_tasks = []

    for device in ADDRESS:
        connection_tasks.append(manage_server(device, config))

    await asyncio.gather(*connection_tasks)

        
            
        

if __name__ == "__main__":
    asyncio.run(main())
