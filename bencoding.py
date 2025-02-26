import re
import itertools as it
import time
from typing import Any, Dict, List, Tuple, Union
from log import Log

# simple bencoding library with added (unofficial) support for floats and tuples.
# tbwcjw 2025

class Bencoding:
    def __init__(self):
        pass

    @staticmethod
    def encode(obj: Any) -> bytes:
        if isinstance(obj, int):
            return b"i" + str(obj).encode() + b"e"
        elif isinstance(obj, float):
            float_str = f"{obj:.10g}"
            return str(len(float_str)).encode() + b":" + float_str.encode()
        elif isinstance(obj, bytes):
            return str(len(obj)).encode() + b":" + obj
        elif isinstance(obj, str):
            return Bencoding.encode(obj.encode('ascii'))
        elif isinstance(obj, list) or isinstance(obj, tuple): 
            if not all(isinstance(item, (int, float, bytes, str, list, dict, tuple)) for item in obj):
                raise BencodingListItemTypesError(f"List items must be one of the allowed types: int, float, bytes, str, list, dict, tuple not {type(obj)}")
            return b"l" + b"".join(map(Bencoding.encode, obj)) + b"e"
        if isinstance(obj, dict):
            byte_key_dict = {k.encode('ascii') if isinstance(k, str) else k: v for k, v in obj.items()}
            if all(isinstance(i, bytes) for i in byte_key_dict.keys()):
                items = byte_key_dict.items()
                encoded_items = b"".join(
                    Bencoding.encode(k) + Bencoding.encode(v) for k, v in items
                )
                return b"d" + encoded_items + b"e"
            else:    
                raise BencodingDictKeyTypeError(f"dict keys should be bytes, not {type(obj)}")
        elif hasattr(obj, 'to_dict'):
            return Bencoding.encode(obj.to_dict())
        
        raise BencodingNotImplementedTypeError(f"Not in implemented types: int, float, bytes, str, list, dict, tuple not {type(obj)}")

    @staticmethod
    def decode(data: bytes) -> Tuple[Union[int, float, str, List[Any], Dict[bytes, Any], Tuple[Any]], bytes]:
        if not isinstance(data, bytes):
            raise BdecodingInputTypeError("Input data must be of type bytes")
         
        if data.startswith(b"i"):
            end = data.find(b"e")
            if end == -1:
                raise BdecodingIntegerInvalidError("Invalid bencoded integer")
            return int(data[1:end].decode()), data[end + 1:]

        elif data[0:1].isdigit():
            colon_index = data.index(b":") if b":" in data else -1
            if colon_index == -1:
                raise BdecodingStringInvalidError("Invalid bencoded string: missing ':'")
            length = int(data[:colon_index].decode())
            start = colon_index + 1
            end = start + length
            if end > len(data):
                raise BdecodingStringLengthError("Invalid bencoded string: declared length exceeds data length")
            
            potential_value_str = data[start:end].decode()
            if Bencoding.is_float_string(potential_value_str):
                return float(potential_value_str), data[end:]

            return potential_value_str, data[end:]

        elif data.startswith(b"l"):
            lst = []
            remaining = data[1:]
            while remaining[0:1] != b"e":
                item, remaining = Bencoding.decode(remaining)
                lst.append(item)
            return tuple(lst), remaining[1:]  

        elif data.startswith(b"d"):
            dct = {}
            remaining = data[1:]
            while remaining[0:1] != b"e":
                key, remaining = Bencoding.decode(remaining)
                value, remaining = Bencoding.decode(remaining)
                dct[key] = value  # keys as bytes
            return dct, remaining[1:]

        raise BdecodingInvalidDataError("Invalid bencoded data")

    @staticmethod
    def is_float_string(s: str) -> bool:
        return re.match(r'^-?\d+(\.\d+)?$', s) is not None


class BencodingListItemTypesError(Exception):
    pass

class BencodingDictKeyTypeError(Exception):
    pass

class BencodingNotImplementedTypeError(Exception):
    pass

class BdecodingInputTypeError(Exception):
    pass

class BdecodingIntegerInvalidError(Exception):
    pass

class BdecodingStringInvalidError(Exception):
    pass

class BdecodingStringLengthError(Exception):
    pass

class BdecodingInvalidDataError(Exception):
    pass