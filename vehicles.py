import os
import pymongo
import configparser

# Convert Dictionaries to MySQL
class MySqlConverter():
    def __init__(self):
        self.ve_cols = ['vehicle_id', 'engine_id']
        self.ee_cols = ['engine_id', 'ecu_id']
        
        self.vehicles = []
        self.engines = []
        self.ecus = []
        
        self.vehicle_engines = []
        self.engine_ecus = []

    def add_vehicles(self, vehicles):
        self.vehicles = vehicles

    def add_engines(self, engines):
        self.engines = engines

    def add_ecus(self, ecus):
        self.ecus = ecus

    def add_vehicle_engines(self, vehicle_engines):
        self.vehicle_engines = vehicle_engines

    def add_engine_ecus(self, engine_ecus):
        self.engine_ecus = engine_ecus
    
    def generate_sql_for(self, name):
        if name != 'all':
            items = getattr(self, name)
            generate_sql(name, name, items)
        else:
            generate_sql('vehicles', 'Vehicles', self.vehicles)
            generate_sql('engines', 'Engines', self.engines)
            generate_sql('ecu', 'ECUs', self.ecus)
            generate_sql_relationship('VehicleEngine', 'VehicleEngine', self.vehicle_engines)
            generate_sql_relationship('EngineEcu', 'EngineEcu', self.engine_ecus)

    def generate_sql_vehicle_engine(self):
        generate_sql_relationship('VehicleEngine', 'VehicleEngine', self.vehicle_engines)

    def generate_sql_engine_ecu(self):
        generate_sql_relationship('EngineEcu', 'EngineEcu', self.engine_ecus)

def generate_sql(tablename, filename, items):
    dir_path = 'sql' + os.sep
    
    try:
        file = open(dir_path + filename + '.sql', 'w')
    except PermissionError:
        print("access denied in creating file!")
        return False
    except IOError:
        print("could not create file!")
        return False
    
    for idx, item in enumerate(items):
        sql = list()
        keys = ['`%s`' % k for k in item.keys()]
        values = ['\'%s\'' % v for v in item.values()]
        primary_index = str(idx + 1) + ', ' 

        sql.append("INSERT INTO `%s` (`id`, " % tablename)
        sql.append(", ".join(keys))
        sql.append(") VALUES (")
        sql.append(primary_index)
        sql.append(", ".join(values))
        sql.append(");")

        file.write("".join(sql))
        file.write("\n")
    file.close()

def generate_sql_relationship(tablename, filename, items):
    dir_path = 'sql' + os.sep

    try:
        file = open(dir_path + filename + '.sql', 'w')

    except PermissionError:
        print("access denied in creating file!")
        return False

    except IOError:
        print("could not create file!")
        return False

    for idx, item in enumerate(items):
        sql = list()
        keys = ['`%s`' % k for k in item.keys()]
        print(keys)
        values = ['%s' % str(v + 1) if v is not None else '' for v in item.values()]
        primary_index = str(idx + 1) + ', ' 

        sql.append("INSERT INTO `%s` (`id`, " % tablename)
        sql.append(", ".join(keys))
        sql.append(") VALUES (")
        sql.append(primary_index)
        sql.append(", ".join(values))
        sql.append(");")

        file.write("".join(sql))
        file.write("\n")
    file.close()

# Transfer Data to MongoDB
class bettermongo():
    def __init__(self, vehicles, engines, ecus, vehicle_engines, engine_ecus):
        self.parsed_vehicles = vehicles
        self.vehicles = list()

        self.parsed_engines = engines
        self.engines = list()

        self.parsed_ecus = ecus
        self.ecus = ecus

        self.parsed_vehicle_engines = vehicle_engines
        self.parsed_engine_ecus = engine_ecus

        self.read_config()
        self.create_mongo()

    def read_config(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        if config['Mongo']:
            self.mongo_host = config['Mongo']['Host']
            self.mongo_port = config['Mongo']['Port']
            self.mongo_db = config['Mongo']['Database']
            self.mongo_username = config['Mongo']['Username']
            self.mongo_password = config['Mongo']['Password']

    def create_mongo(self):
        connection_string = 'mongodb://' + self.mongo_username + ':' + self.mongo_password + '@' + self.mongo_host + ':' + self.mongo_port + '/' + self.mongo_db

        self.mongoclient = pymongo.MongoClient(connection_string)
        self.db = self.mongoclient[self.mongo_db]

    def unify_engines_ecus(self):
        for engine in self.parsed_engines:
            engine['ecus'] = list()
            self.engines.append(engine)

        for p_engine in self.parsed_engine_ecus:
            if p_engine['engine_id'] is not None and p_engine['ecu_id'] is not None:
                engine = self.engines[int(p_engine['engine_id'])]
                ecu = self.parsed_ecus[int(p_engine['ecu_id'])]

                if ecu not in engine['ecus']:
                    engine['ecus'].append(ecu)

    def unify_vehicle_engines(self):
        for vehicle in self.parsed_vehicles:
            vehicle['engines'] = list()
            self.vehicles.append(vehicle)

        for p_vehicle_engine in self.parsed_vehicle_engines:
            if p_vehicle_engine['vehicle_id'] is not None and p_vehicle_engine['engine_id'] is not None:
                vehicle = self.vehicles[int(p_vehicle_engine['vehicle_id'])]
                engine = self.engines[int(p_vehicle_engine['engine_id'])]

                if engine not in vehicle['engines']:
                    vehicle['engines'].append(engine)

    def print_items(self, items):
        for item in items:
            print(item)
            print("\n")

    def add_mongo(self):
        print('Adding to MongoDB:')
        self.unify_engines_ecus()
        self.unify_vehicle_engines()
        self.print_items(self.vehicles)
        
        result = self.db.vehicles.insert_many(self.vehicles)
        print(result)

