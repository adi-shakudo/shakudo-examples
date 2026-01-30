import os
import re
import json
import argparse
from datetime import datetime
import pyodbc
import pandas as pd

# ---- copy of your mapping (keep in-sync with config.py) ----
RESORT_MAPPING = [
    {"dbName": "Purgatory", "resortName": "PURGATORY", "groupNum": 46},
    {"dbName": "Purgatory", "resortName": "HESPERUS", "groupNum": 54},
    {"dbName": "Purgatory", "resortName": "SNOWCAT", "groupNum": 59},
    {"dbName": "Purgatory", "resortName": "SPIDER MOUNTAIN", "groupNum": 67},
    {"dbName": "Purgatory", "resortName": "DMMA", "groupNum": 70},
    {"dbName": "Purgatory", "resortName": "WILLAMETTE", "groupNum": 71},
    {"dbName": "MCP", "resortName": "PAJARITO", "groupNum": 9},
    {"dbName": "MCP", "resortName": "SANDIA", "groupNum": 10},
    {"dbName": "MCP", "resortName": "WILLAMETTE", "groupNum": 12},
    {"dbName": "Snowbowl", "resortName": "Snowbowl", "groupNum": -1},
    {"dbName": "Lee Canyon", "resortName": "Lee Canyon", "groupNum": -1},
    {"dbName": "Sipapu", "resortName": "Sipapu", "groupNum": -1},
    {"dbName": "Nordic", "resortName": "Nordic", "groupNum": -1},
    {"dbName": "Brian", "resortName": "Brian", "groupNum": -1},
]

STORED_PROCS = {
    "revenue": "exec Shakudo_DMRGetRevenue @database=?, @group_no=?, @date_ini=?, @date_end=?",
    "payroll": "exec Shakudo_DMRGetPayroll @resort=?, @date_ini=?, @date_end=?",
    "payroll_salary": "exec Shakudo_DMRGetPayrollSalary @resort=?, @date_ini=?, @date_end=?",
    "payroll_history": "exec Shakudo_DMRGetPayrollHistory @resort=?, @date_ini=?, @date_end=?",
    "budget": "exec Shakudo_DMRBudget @resort=?, @date_ini=?, @date_end=?",
    "visits": "exec Shakudo_DMRGetVists @resort=?, @date_ini=?, @date_end=?",
    "weather": "exec Shakudo_GetSnow @resort=?, @date_ini=?, @date_end=?",
}

def safe_name(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")

def cursor_to_df(cur) -> pd.DataFrame:
    cols = [c[0] for c in cur.description] if cur.description else []
    rows = cur.fetchall()
    return pd.DataFrame.from_records(rows, columns=cols)

def connect() -> pyodbc.Connection:
    username = os.environ["MCP_DB_USERNAME"]
    password = os.environ["MCP_DB_PASSWORD"]
    server   = os.environ["MCP_DB_SERVER"]
    port     = os.environ.get("MCP_DB_PORT", "1433")
    dbname   = os.environ["MCP_DB_NAME"]

    driver = "ODBC Driver 18 for SQL Server"
    # NOTE: your config had TlsVersion=1.1; that can break on newer servers.
    # If you MUST force a TLS version, add it back, but try without first.
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server},{port};"
        f"DATABASE={dbname};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=60;"
    )
    return pyodbc.connect(conn_str)

def run_proc(cur, proc_key: str, m: dict, date_start: str, date_end: str) -> pd.DataFrame:
    sql = STORED_PROCS[proc_key]
    if proc_key == "revenue":
        # revenue uses: (database, group_number, date_start, date_end)
        params = (m["dbName"], int(m["groupNum"]), date_start, date_end)
    else:
        # others use: (resort_name, date_start, date_end)
        params = (m["resortName"], date_start, date_end)

    cur.execute(sql, params)
    return cursor_to_df(cur)

def write_df(df: pd.DataFrame, out_path: str, metadata: dict):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # add light lineage columns (helps debugging)
    for k, v in metadata.items():
        df[f"_meta_{k}"] = v
    df.to_parquet(out_path, index=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--date-start", required=True)
    ap.add_argument("--date-end", required=True)
    ap.add_argument("--procs", required=True, help="comma-separated keys: " + ",".join(STORED_PROCS.keys()))
    args = ap.parse_args()

    outdir = args.outdir
    date_start = args.date_start
    date_end = args.date_end
    selected = [p.strip() for p in args.procs.split(",") if p.strip()]
    for p in selected:
        if p not in STORED_PROCS:
            raise SystemExit(f"Unknown proc '{p}'. Valid: {list(STORED_PROCS.keys())}")

    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    conn = connect()
    try:
        cur = conn.cursor()

        for m in RESORT_MAPPING:
            resort = safe_name(m["resortName"])
            dbname = safe_name(m["dbName"])
            group  = str(m["groupNum"])

            for proc_key in selected:
                # skip revenue for resorts with groupNum=-1 (if that's your rule)
                if proc_key == "revenue" and int(m["groupNum"]) < 0:
                    continue

                df = run_proc(cur, proc_key, m, date_start, date_end)

                # folder partitioning (Dremio-friendly):
                # <outdir>/proc=<proc>/db=<db>/resort=<resort>/date_start=YYYY-MM-DD/date_end=YYYY-MM-DD/run_id=.../part-000.parquet
                base = os.path.join(
                    outdir,
                    f"proc={proc_key}",
                    f"db={dbname}",
                    f"resort={resort}",
                    f"date_start={date_start}",
                    f"date_end={date_end}",
                    f"run_id={run_id}",
                )
                out_path = os.path.join(base, "part-000.parquet")

                meta = {
                    "proc": proc_key,
                    "db": m["dbName"],
                    "resort": m["resortName"],
                    "groupNum": group,
                    "date_start": date_start,
                    "date_end": date_end,
                    "run_id": run_id,
                    "rowcount": str(len(df)),
                }

                print(json.dumps({"writing": out_path, "rows": len(df)}))
                write_df(df, out_path, meta)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
