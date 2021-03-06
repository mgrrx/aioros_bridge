from typing import Any, Dict, Type

from genpy import Duration, Time

from aioros.abc import Message


def import_msg_class(msg_type: str) -> Type[Message]:
    module_name, cls_name = msg_type.split("/")
    return getattr(getattr(__import__(module_name + ".msg"), "msg"), cls_name)


def to_dict(msg: Message) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for key in msg.__slots__:
        value = getattr(msg, key)
        if isinstance(value, (Time, Duration)):
            data[key] = dict(secs=value.secs, nsecs=value.nsecs)
        elif isinstance(value, Message):
            data[key] = to_dict(value)
        elif isinstance(value, list):
            if len(value) == 0:
                data[key] = value
            elif isinstance(value[0], (Time, Duration)):
                data[key] = [dict(secs=i.secs, nsecs=i.nsecs) for i in value]
            elif isinstance(value[0], Message):
                data[key] = [to_dict(i) for i in value]
            else:
                data[key] = value
        else:
            data[key] = value
    return data
