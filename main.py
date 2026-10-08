# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 18:52:40 2026

@author: m.razakasoa
"""

import pandas as pd
import pyodbc

from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pyodbc://Minonja:Minonja@172.20.24.37/RECONCILIATION_DFS?driver=SQL+Server"
)





df = pd.read_excel('not_found_request_id.xlsx')


df.to_sql(
    name='not_found_request_id',  # table name
    con=engine,
    if_exists='replace',  # 'replace' or 'append'
    index=False
)