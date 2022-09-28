import json
from common.exception.invalid_json_exception import InvalidJsonException


class JsonFileUtil:
    def __init__(self, *, file_name_with_path: str):
        self.file_name_with_path = file_name_with_path

    def read_file(self) -> dict:
        with open(self.file_name_with_path) as f:
            try:
                return json.load(f)
            except Exception as e:
                raise InvalidJsonException(e)
