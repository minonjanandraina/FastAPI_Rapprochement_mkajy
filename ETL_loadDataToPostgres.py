# action list:

# Step 1: in staging are folder ./staggingAre/TANGO loan the 3 type of transaction to database table 
# Step 2 : load reconciliation result to 2 tables (transaction from OM and transaction from FRONT) in the database, 

#Next in other modules we will do the following steps:
# Step 3 : create a cron job to run the reconciliation process every day and to load the reconciliation result to the database,
#Step 4 : create a backend api with django rest in upped directory (BACKEND) to expose the reconciliation result and to manage failed transactions,
#Step 5 : create a dashboard to show the reconciliation result and to manage failed transactions with react js in upped directory (FRONTEND)

import pandas as pd
from datetime import date
from psycopg2 import sql
def getConnection():
    import psycopg2
    from psycopg2 import sql
    conn = psycopg2.connect(
        host="192.168.123.97",
        database="transfix",
        user="admin",
        password="root@dfs2024",
        port=5432
    )
    return conn

def normalize_tango_df(df):
    df = df.rename(columns={

        "Date": "trx_date",
        "Heure": "trx_time",
        "OMTransactionID": "om_transaction_id",
        "Service": "service",
        "Statut": "status",
        "technical_account": "technical_account",
        "debit": "debit",
        "credit": "credit",
        "TransactionDatetime": "transaction_datetime",
        "tango_reconciliation_status": "tango_reconciliation_status",
    })

    for col in ["debit", "credit"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    if "technical_account" in df.columns:
        df["technical_account"] = df["technical_account"].astype(str)

    if "trx_date" in df.columns:
        df["trx_date"] = pd.to_datetime(df["trx_date"], format="%d/%m/%Y", errors="coerce").dt.date

    if "trx_time" in df.columns:
        df["trx_time"] = pd.to_datetime(df["trx_time"], format="%H:%M:%S", errors="coerce").dt.time

    if "transaction_datetime" in df.columns:
        df["transaction_datetime"] = pd.to_datetime(df["transaction_datetime"], errors="coerce")

    return df
#Step 1 : in staging are folder ./staggingAre/TANGO loan the 3 type of transaction to database table
def load_data_to_postgres(d):
    col=['trx_date', 'trx_time', 'om_transaction_id', 'service', 'status', 'technical_account', 'debit', 'credit', 'transaction_datetime', 'tango_reconciliation_status']
    filepath_tango_transaction = f"./staggingArea/TANGO/DailyTangoTransaction-mkajy- {d:%Y%m%d}.csv"
    filepath_tango_manual = f"./staggingArea/TANGO/DailyTangoTransaction-manual- {d:%Y%m%d}.csv"
    filepath_tango_rollback = f"./staggingArea/TANGO/DailyTangoTransaction-rollback- {d:%Y%m%d}.csv"

    df_tango_transaction = pd.read_csv(filepath_tango_transaction)
    df_tango_manual = pd.read_csv(filepath_tango_manual)    
    df_tango_rollback = pd.read_csv(filepath_tango_rollback)
    
    df_tango_rollback['tango_reconciliation_status'] = 'Rollback Transaction'
    df_tango_manual['tango_reconciliation_status'] = 'Manual Transaction'
    df_tango_transaction['tango_reconciliation_status'] = 'Normal Transaction'

    df_tango_transaction = normalize_tango_df(df_tango_transaction)
    df_tango_manual = normalize_tango_df(df_tango_manual)
    df_tango_rollback = normalize_tango_df(df_tango_rollback)
    
    df_tango_transaction=df_tango_transaction[col]
    df_tango_manual=df_tango_manual[col]
    df_tango_rollback=df_tango_rollback[col]

    conn = getConnection()
    cursor = conn.cursor()
    
    for df, table_name in [(df_tango_transaction, "rec_tango_transaction"), (df_tango_manual, "rec_tango_transaction"), (df_tango_rollback, "rec_tango_transaction")]:
        for _, row in df.iterrows():
            columns = list(row.index)
            values = [row[col] for col in columns]
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(values))
            )
            cursor.execute(insert_query, values)
    
    conn.commit()
    cursor.close()
    conn.close()
    

    #test df to check data type to fit with database table
    return df_tango_transaction, df_tango_manual, df_tango_rollback




    
dateFrom = date(2026, 1, 18)
dateTo = date(2026, 2, 5)
list_date = pd.date_range(start=dateFrom, end=dateTo).tolist()

for d in list_date:
    #make pretty print
    print("\n" + "=" * 60)
    print(f"📅 LOADING DATA FOR DATE : {d:%Y-%m-%d}")
    df_tango_transaction, df_tango_manual, df_tango_rollback = load_data_to_postgres(d)
    print(f"✅ DATA LOADED FOR DATE : {d:%Y-%m-%d}")
