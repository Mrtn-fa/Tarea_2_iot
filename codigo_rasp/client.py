from bleak import BleakScanner, BleakClient
from modelos import create_tables
from modelos import Configuration
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


class ClientHandler:
    def __init__(self):
        self.scanner = BleakScanner()
        self.client = None
        self.config = Config()

    def get_config(self):
        return self.config.get()

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


if __name__ == "__main__":
    c = ClientHandler()
    print(TAG, "Revisando las posibles conexiones...")
    devices = asyncio.run(c.discover())
    print(TAG, "Dispostivos descubiertos:")
    for i, d in enumerate(devices):
        print(i, d)
    
    i = int(input("Escoge un dispositivo para conectarte: "))
    selected_mac = devices[i]
    asyncio.run(c.connect(selected_mac))
    print(TAG, "Conectado a", selected_mac)

    actual_config = c.get_config()
    print(TAG, "La configuración es", actual_config)

    # TODO: enviar actual config
    asyncio.run(c.char_write(CHAR_CONFIG, actual_config))
