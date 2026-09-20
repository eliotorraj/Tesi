"""Serializzazione tabellare senza perdita: campi e valori restano ricostruibili."""
from __future__ import annotations
import json
MARKER_KEYS={"$columns","$rows"}
INSTRUCTION=("In the input only, an object with exactly $columns and $rows represents a list of objects. "
             "Each row has one value for each column, in the same order. Nested tables follow the same rule. "
             "Every original field and value is included. The response must follow response_contract, not this table notation.")

def pack(value):
    if isinstance(value,list):
        if len(value)>=4 and all(isinstance(row,dict) for row in value):
            columns=list(value[0])
            if columns and all(set(row)==set(columns) for row in value):
                return {"$columns":columns,"$rows":[[pack(row[k]) for k in columns] for row in value]}
        return [pack(item) for item in value]
    if isinstance(value,dict):
        if set(value)==MARKER_KEYS: raise ValueError("Reserved table marker collides with input")
        return {key:pack(item) for key,item in value.items()}
    return value

def unpack(value):
    if isinstance(value,dict):
        if set(value)==MARKER_KEYS:
            columns=value["$columns"]
            if len(columns)!=len(set(columns)) or any(len(row)!=len(columns) for row in value["$rows"]):
                raise ValueError("Malformed table")
            return [{key:unpack(item) for key,item in zip(columns,row)} for row in value["$rows"]]
        return {key:unpack(item) for key,item in value.items()}
    if isinstance(value,list): return [unpack(item) for item in value]
    return value

def encode_prompt(prompt):
    packed={key:(value if key=="response_contract" else pack(value)) for key,value in prompt.items()}
    # Exact equality covers all nested fields, floats, QASM strings and evidence identifiers.
    if unpack(packed)!=prompt: raise ValueError("Lossless prompt round-trip failed")
    return json.dumps(packed,ensure_ascii=False,separators=(",",":"))
