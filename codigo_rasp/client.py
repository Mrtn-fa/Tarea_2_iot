from bleak import BleakScanner, BleakClient
from bleak import exc
from modelos import create_tables
from modelos import Configuration
from time import sleep
from peewee import DoesNotExist
import asyncio
from threading import Thread

TAG = "[RASP]"

CHAR_CONFIG = "0xFF01"

print(TAG, "Creando tablas")
create_tables()

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


async def manage_server(client, config):
    actual_config = config.get()
    while actual_config[0] == 0:
        print(TAG, "La configuración es", actual_config)
        # se pasa la configuracion
        actual_config = f"con{actual_config[0]}{actual_config[1]}"
        await client.write_gatt_char(CHARACTERISTIC_UUID, actual_config.encode())

        # recibe datos
        res = await client.read_gatt_char(CHARACTERISTIC_UUID)
        print(f"Se leyo: {res}")

        # los guarda segun lo protocolo
        # queda por hacer

        actual_config = config.get()

def execute(client, config):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(manage_server(client, config))

async def main():
    config = Config()

    ADDRESS = ["3c:61:05:65:47:22"]


    while True:
        for device in ADDRESS:
            try:
                async with BleakClient(device) as client:
                    thread = Thread(target=execute,args=(client, config))
                    print("iniciando el thread")
                    thread.start()
            except exc.BleakDeviceNotFoundError:
                pass
            
        
            
        

if __name__ == "__main__":
    asyncio.run(main())
