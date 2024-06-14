import time
from dataclasses import dataclass
from functools import lru_cache

import httpx

BASE = 'https://game.maj-soul.com/1'


def fetch_version() -> str:
    url = f'{BASE}/version.json'
    obj = httpx.get(url).json()
    return obj.get('version')


def fetch_resource() -> dict:
    ver = fetch_version()
    url = f'{BASE}/resversion{ver}.json'
    obj = httpx.get(url).json()
    return obj


def fetch_riichi() -> dict:
    path = 'res/proto/liqi.json'
    res = fetch_resource()
    pre = res['res'][path]['prefix']
    url = f'{BASE}/{pre}/{path}'
    obj = httpx.get(url).json()
    return obj


@dataclass
class Field:
    id: int
    name: str
    type: str
    rule: str


@dataclass
class Method:
    name: str
    input: str
    output: str


@dataclass
class Value:
    name: str
    number: int


@dataclass
class Enum:
    name: str
    values: list[Value]


@dataclass
class Message:
    name: str
    fields: list[Field]
    nested: list['Message']


@dataclass
class Service:
    name: str
    methods: list[Method]


@dataclass
class Proto:
    name: str
    enums: list[Enum]
    services: list[Service]
    messages: list[Message]


def _parse_enums(json: dict[str, dict]):
    def _parse_values(values: dict[str, int]):
        for name, number in values.items():
            yield Value(name=name, number=number)

    for name, spec in json.items():
        if 'values' in spec:
            yield Enum(
                name=name,
                values=sorted(_parse_values(spec['values']), key=lambda v: v.number),
            )


def _parse_services(json: dict[str, dict]):
    def _parse_methods(methods: dict[str, dict]):
        for name, spec in methods.items():
            yield Method(
                name=name, input=spec['requestType'], output=spec['responseType']
            )

    for name, spec in json.items():
        if 'methods' in spec:
            yield Service(
                name=name,
                methods=sorted(_parse_methods(spec['methods']), key=lambda m: m.name),
            )


def _parse_messages(json: dict[str, dict]):
    def _parse_fields(fields: dict[str, dict]):
        for name, spec in fields.items():
            yield Field(
                id=spec['id'], name=name, type=spec['type'], rule=spec.get('rule', '')
            )

    for name, spec in json.items():
        if 'fields' in spec:
            nested = _parse_messages(spec['nested']) if 'nested' in spec else []

            yield Message(
                name=name,
                nested=sorted(nested, key=lambda f: f.name),
                fields=sorted(_parse_fields(spec['fields']), key=lambda f: f.id),
            )


@lru_cache(maxsize=2)
def parse_riichi(key):
    obj = fetch_riichi()

    riichi_json = obj['nested']['lq']['nested']

    return Proto(
        name='riichi',
        enums=sorted(_parse_enums(riichi_json), key=lambda e: e.name),
        services=sorted(_parse_services(riichi_json), key=lambda s: s.name),
        messages=sorted(_parse_messages(riichi_json), key=lambda m: m.name),
    )


def query_proto():
    def _key():  # ugly time to live implementation
        return int(time.time() / 3600 / 24)

    return parse_riichi(_key())
