import sqlalchemy


def to_dict(obj):
    return {c.key: getattr(obj, c.key) for c in sqlalchemy.inspect(obj).mapper.column_attrs}


def parse_format(value: str):
    multiplier_mapping = {'K': 1000, 'M': 1000000}
    last_character = value[-1].upper()
    multiplier = multiplier_mapping.get(last_character, 1)
    value = value[:-1] if last_character in multiplier_mapping else value
    return int(float(value) * multiplier)
