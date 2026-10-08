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

#here we will load 2 type of transaction: 
#1- transaction OM in output/reconciliation: filename example : reconciliation_om-mkajy-2026-01-03.csv
#2- transaction Front in output/reconciliation: filename example : reconciliation_front-mkajy-2026-01-21.csv

def normalize_reconciliation_om_df(df):
    df = df.rename(columns={
        "Date": "trx_date",
        "Heure": "trx_time",
        "OMTransactionID": "om_transaction_id",
        "Service": "service",
        "Status": "status",
        "technical_account": "technical_account",
        "debit": "debit",
        "credit": "credit",
        "TransactionDatetime": "transaction_datetime",
        "transaction_type": "transaction_type",
        "operationID": "operation_id",
        "RequestId": "request_id",
        "mcTransactionID": "mc_transaction_id",
        "rAutoTransactionID": "r_auto_transaction_id",
        "transactionAmount": "transaction_amount",
        "CheckAmount": "check_amount",
        "reconciliation_status": "reconciliation_status",
    })

    numeric_cols = [
        "debit",
        "credit",
        "transaction_amount",
        "check_amount",
        "mc_transaction_id",
        "r_auto_transaction_id",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(0)


    if "technical_account" in df.columns:
        df["technical_account"] = df["technical_account"].astype(str)

    if "request_id" in df.columns:
        df["request_id"] = df["request_id"].astype(str)

    if "trx_date" in df.columns:
        df["trx_date"] = pd.to_datetime(df["trx_date"], format="%Y-%m-%d", errors="coerce").dt.date

    if "trx_time" in df.columns:
        df["trx_time"] = pd.to_datetime(df["trx_time"], format="%H:%M:%S", errors="coerce").dt.time

    if "transaction_datetime" in df.columns:
        df["transaction_datetime"] = pd.to_datetime(df["transaction_datetime"], errors="coerce")

    return df


def normalize_reconciliation_front_df(df):
    df = df.rename(columns={
        "RequestId": "request_id",
        "rAutoTransactionID": "r_auto_transaction_id",
        "documentID": "document_id",
        "transactionAmount": "transaction_amount",
        "RequestDateCreated": "request_date_created",
        "rTransactionTypeID": "r_transaction_type_id",
        "mcTransactionID": "mc_transaction_id",
        "apiLogId": "api_log_id",
        "technical_account": "technical_account",
        "OMTransactionID": "om_transaction_id",
        "debit": "debit",
        "credit": "credit",
        "CheckAmount": "check_amount",
        "reconciliation_status": "reconciliation_status",
    })

    numeric_cols = [
        "debit",
        "credit",
        "transaction_amount",
        "check_amount",
        "document_id",
        "r_transaction_type_id",
        "mc_transaction_id",
        "api_log_id",
        "r_auto_transaction_id",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(0)

    if "technical_account" in df.columns:
        df["technical_account"] = df["technical_account"].astype(str)

    if "request_id" in df.columns:
        df["request_id"] = df["request_id"].astype(str)

    if "request_date_created" in df.columns:
        df["request_date_created"] = pd.to_datetime(df["request_date_created"], errors="coerce")

    return df

def load_reconciliation_to_postgres(date, transaction_type):
    # Read the CSV file into a DataFrame
    filename = f"./output/reconciliation/reconciliation_{transaction_type}-mkajy-{date:%Y-%m-%d}.csv"
    df = pd.read_csv(filename)
    
    # Establish a connection to the PostgreSQL database
    conn = getConnection()
    cursor = conn.cursor()
    
    # Define the table name based on transaction type
    if transaction_type == 'om':
        table_name = 'rec_om'
        df = normalize_reconciliation_om_df(df)
    elif transaction_type == 'front':
        table_name = 'rec_front'
        df = normalize_reconciliation_front_df(df)
    else:
        return False  # Invalid transaction type
    
    # Insert data into the PostgreSQL table using CSV columns
    columns = list(df.columns)
    column_identifiers = sql.SQL(", ").join([sql.Identifier(col) for col in columns])
    placeholders = sql.SQL(", ").join([sql.Placeholder()] * len(columns))

    insert_query = sql.SQL("""
        INSERT INTO {} ({}) VALUES ({})
    """).format(sql.Identifier(table_name), column_identifiers, placeholders)

    for _, row in df.iterrows():
        values = tuple(row[col] for col in columns)
        cursor.execute(insert_query, values)
    
    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()
    return True 

# Uses all columns from the CSV header for inserts.
    
dateFrom = date(2026, 1, 1)
dateTo = date(2026, 2, 5)
list_date = pd.date_range(start=dateFrom, end=dateTo).tolist()
i=0
for d in list_date:
    #make pretty print
    print("\n" + "=" * 60)
    print(f"📅 LOADING DATA FOR DATE : {d:%Y-%m-%d}")
    if i>0:
        result = load_reconciliation_to_postgres(d,'front')
        if result:
            print(f"✅ DATA FRONT  LOADED  FOR DATE : {d:%Y-%m-%d}")
        else:
            print(f"❌ FAILED  TO LOAD DATA FRONT FOR DATE : {d:%Y-%m-%d}")
            
    result = load_reconciliation_to_postgres(d,'om')
    if result:
        print(f"✅ DATA OM LOADED FOR DATE : {d:%Y-%m-%d}")
    else:
        print(f"❌ FAILED TO LOAD DATA OM FOR DATE : {d:%Y-%m-%d}")
    i+=1
        