"""Strict JSON decoding shared by dataset and model boundaries."""
import json
import math


def loads(text):
    def reject_constant(value):
        raise ValueError(f'Non-finite JSON number: {value}')
    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('JSON number outside finite range')
        return result
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(text, parse_constant=reject_constant, parse_float=finite_float,
                      object_pairs_hook=unique_object)
