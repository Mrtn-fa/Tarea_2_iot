from bleak import BleakScanner, BleakClient
from modelos import create_tables
from modelos import Configuration
from time import sleep
from peewee import DoesNotExist
import asyncio

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


async def main():
    config = Config()

    ADDRESS = "3c:61:05:65:47:22"
    async with BleakClient(ADDRESS) as client:
    

        actual_config = config.get()
        print(TAG, "La configuración es", actual_config)
        await client.read_gatt_char(CHARACTERISTIC_UUID)
        await client.write_gatt_char(CHARACTERISTIC_UUID, b"Hola")
        

if __name__ == "__main__":
    asyncio.run(main())
