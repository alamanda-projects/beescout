# # # =======================
# # # Project : BeeScout Repository
# # # Author  : Alamanda Team
# # # File    : app/model/display.py
# # # Function: Displaying model data
# # # =======================

from fastapi import HTTPException
from app.model.all import *
# from app.model.dbschema import *
from app.core.connection import database, col_dgr
from app.info.app_info import dc_404

dccollection = database[col_dgr]
dc_404_notfound = HTTPException(status_code=404, detail=dc_404)


async def display_all(contract_number: str = None):
    query = {}
    if contract_number:
        query["contract_number"] = contract_number
        dcfilter = await dccollection.find(query).to_list(None)
    else:
        dcfilter = await dccollection.find().to_list(None)

    if not dcfilter:
        raise dc_404_notfound
    dcfilter = [All(**all) for all in dcfilter]
    return dcfilter


async def display_metadata(contract_number: str = None):
    query = {}
    if contract_number:
        query["contract_number"] = contract_number
        dcfilter = await dccollection.find(query).to_list(None)
    else:
        dcfilter = await dccollection.find().to_list(None)

    if not dcfilter:
        raise dc_404_notfound

    dcfilter = [Metadatas(**all) for all in dcfilter]
    return dcfilter


async def display_model(contract_number: str = None):
    query = {}
    if contract_number:
        query["contract_number"] = contract_number
        dcfilter = await dccollection.find(query).to_list(None)
    else:
        dcfilter = await dccollection.find().to_list(None)

    if not dcfilter:
        raise dc_404_notfound

    dcfilter = [Models(**all) for all in dcfilter]
    return dcfilter


async def display_ports(contract_number: str = None):
    query = {}
    if contract_number:
        query["contract_number"] = contract_number
        dcfilter = await dccollection.find(query).to_list(None)
    else:
        dcfilter = await dccollection.find().to_list(None)

    if not dcfilter:
        raise dc_404_notfound

    dcfilter = [Ports(**all) for all in dcfilter]
    return dcfilter


async def display_examples(contract_number: str = None):
    query = {}
    if contract_number:
        query["contract_number"] = contract_number
        dcfilter = await dccollection.find(query).to_list(None)
    else:
        dcfilter = await dccollection.find().to_list(None)

    if not dcfilter:
        raise dc_404_notfound
    dcfilter = [Examples(**all) for all in dcfilter]

    return dcfilter


async def display_dbtschema(contract_number: str = None):
    query = {}
    if contract_number:
        query["contract_number"] = contract_number
        dcfilter = await dccollection.find(query).to_list(None)
    else:
        dcfilter = await dccollection.find().to_list(None)

    if not dcfilter:
        raise dc_404_notfound
    dcfilter = [Dbtschema(**all) for all in dcfilter]

    return dcfilter
