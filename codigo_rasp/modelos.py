from peewee import *

# Configuración de la base de datos
db_config = {
    'host': '0.0.0.0', 
    'port': 5432, 
    'user': 'postgres', 
    'password': 'postgres', 
    'database': 'iot_db'
}
db = PostgresqlDatabase(**db_config)

# Definición de un modelo
class BaseModel(Model):
    class Meta:
        database = db

class Datos(BaseModel):
    # HEADER
    header_id = IntegerField()
    header_mac = CharField(max_length=30)
    transport_layer = CharField(max_length=3)
    id_protocol = IntegerField()
    length = IntegerField()

    # BODY
    batt_level = IntegerField(null=True)
    temp = IntegerField(null=True)
    press = IntegerField(null=True)
    hum = IntegerField(null=True)
    co = FloatField(null=True)
    rms = FloatField(null=True)
    amp_x = FloatField(null=True)
    frec_x = FloatField(null=True)
    amp_y = FloatField(null=True)
    frec_y = FloatField(null=True)
    amp_z = FloatField(null=True)
    frec_z = FloatField(null=True)
    
    timestamp = IntegerField(null=True)
    id_device = CharField()

class Logs(BaseModel):
    id_device = CharField()
    transport_layer = IntegerField(null=True)
    id_protocol = IntegerField(null=True)
    timestamp = DateTimeField()

class Configuration(BaseModel):
    id_protocol = IntegerField()
    transport_layer = IntegerField()

class Loss(BaseModel):
    delay = FloatField() # ms
    packet_loss = IntegerField()


def create_tables():
    with db:
        db.create_tables([Datos, Logs, Configuration, Loss])
        print("tablas creadas")