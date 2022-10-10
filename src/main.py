from glob import glob
from pathlib import Path
import orjson
from jsonschema import validate

def retrieve_dict(file_path: str) -> dict:
    with open(file_path, 'rb') as myfile:
        myjson = orjson.loads(myfile.read())
        myfile.close()
    return myjson

def save_dict(file_path: str, myjson: dict) -> None:
    with open(file_path, 'wb') as myfile:
        myfile.write(orjson.dumps(myjson))
        myfile.close()
    return

def process_schema(entity_json: dict) -> dict:
    def select_type_from_value(value) -> str:
        python_type = type(value).__name__ 
        if python_type == 'str':
            return 'string'
        elif python_type == 'int':
            return 'number'
        elif python_type == 'float':
            return 'number'
        elif python_type == 'bool':
            return 'boolean'
        return 'string' # default to string on null

    def handle_base_types(base_value) -> dict:
        return {'type': select_type_from_value(base_value)}

    def handle_object(entity_json_nest: dict) -> dict:
        nested_schema_json = {'type': 'object', 'properties': {}}
        for key in entity_json_nest.keys():
            if isinstance(entity_json_nest[key], dict):
                nested_schema_json['properties'][key] = handle_object(entity_json_nest[key])
            elif isinstance(entity_json_nest[key], list):
                nested_schema_json['properties'][key] = handle_list(entity_json_nest[key])
            else:
                nested_schema_json['properties'][key] = handle_base_types(entity_json_nest[key])
        return nested_schema_json

    def handle_list(list_entity: list) -> dict:
        nested_schema_json = {'type': 'array', 'items': {}}
        if len(list_entity) > 0:
            if isinstance(list_entity[0], dict):
                nested_schema_json['items'] = handle_object(list_entity[0])
            elif isinstance(list_entity[0], list):
                nested_schema_json['items'] = handle_list(list_entity[0])
            else:
                nested_schema_json['items'] = handle_base_types(list_entity[0])

        return nested_schema_json

    schema_json = {"$schema": "http://json-schema.org/draft-04/schema#", "type": "object", "properties": {}, "$defs": {}}
    for key in entity_json.keys():
        if isinstance(entity_json[key], dict): # send the entity to a function which iterates the keys and creates a schema
            schema_json['properties'][key] = handle_object(entity_json[key])
        elif isinstance(entity_json[key], list):
            schema_json['properties'][key] = handle_list(entity_json[key])
        else:
            schema_json['properties'][key] = handle_base_types(entity_json[key])

    validate({}, schema_json)
    return schema_json

full_data_path = '../processed_json'
if Path(full_data_path).exists():
    files = glob(f'{full_data_path}/*.json')
    for file in files:
        entity_json = retrieve_dict(file)
        schema_json = process_schema(entity_json)
        save_dict(file.split('/')[-1], schema_json)
print('complete')
