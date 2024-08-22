import csv
import datetime
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Literal, Tuple

INPUT_NAWALLET_BACKUP_FILE_PATH = "data/MoneyKeeper.db"
OUTPUT_ICOST_IMPORT_FILE_PATH = "data/iCost.csv"

RECORD_TYPE_MAP: Dict[int, Tuple[str, str]] = {
    1: ("餐饮", "三餐"),
    2: ("餐饮", "零食"),
    3: ("餐饮", "水果"),
    4: ("日用", ""),
    5: ("交通", ""),
    7: ("住房", "水电费"),
    9: ("购物", ""),
    10: ("娱乐", ""),
    16: ("医疗", ""),
    17: ("人情", "礼金"),
    20: ("通讯", ""),
    21: ("人情", ""),
    22: ("学习", ""),
    24: ("人情", "捐赠"),
    27: ("其他", ""),
    28: ("奖金", ""),
    29: ("红包", ""),
    30: ("投资", ""),
    31: ("餐饮", "三餐"),
    32: ("其他", ""),
    33: ("娱乐", ""),
    34: ("其他", ""),
    35: ("兼职", ""),
    36: ("其他", ""),
    37: ("其他", ""),
}

ASSETS_MAP: Dict[int, str] = {
    -1: "现金钱包",
    1: "储蓄卡中国银行1",
    2: "现金钱包",
    3: "现金钱包",
    4: "微信钱包1",
    5: "支付宝",
    6: "现金钱包",
    7: "现金钱包",
    8: "饭卡",
    9: "信用卡中国银行1",
    10: "现金钱包",
}


@dataclass
class NaWalletRow:
    id: int
    money: int
    remark: str
    time: int
    create_time: int
    record_type_id: int
    assets_id: int


@dataclass
class ICostRow:
    date: str
    type: Literal["支出", "收入", "转账"]
    amount: float
    category: str
    subcategory: str
    account_1: str
    account_2: str
    note: str
    currency: str
    tags: str


def load_nawallet_assets(cursor: sqlite3.Cursor) -> Dict[int, str]:
    cursor.execute("SELECT * FROM Assets")
    rows = cursor.fetchall()
    return {row[0]: row[1] for row in rows}


def load_nawallet_record_types(cursor: sqlite3.Cursor) -> Dict[int, Tuple[str, int]]:
    cursor.execute("SELECT * FROM RecordType")
    rows = cursor.fetchall()
    return {row[0]: (row[1], row[3]) for row in rows}


def load_nawallet_records(cursor: sqlite3.Cursor) -> List[NaWalletRow]:
    cursor.execute("SELECT * FROM Record")
    rows = cursor.fetchall()
    return [NaWalletRow(*row) for row in rows]


def save_icost_rows(rows: List[ICostRow], save_path: str) -> None:
    with open(save_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "日期",
                "类型",
                "金额",
                "一级分类",
                "二级分类",
                "账户1",
                "账户2",
                "备注",
                "货币",
                "标签",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.date,
                    row.type,
                    row.amount,
                    row.category,
                    row.subcategory,
                    row.account_1,
                    row.account_2,
                    row.note,
                    row.currency,
                    row.tags,
                ]
            )


def main():
    conn = sqlite3.connect(INPUT_NAWALLET_BACKUP_FILE_PATH)
    cursor = conn.cursor()

    nawallet_assets = load_nawallet_assets(cursor)
    nawallet_record_types = load_nawallet_record_types(cursor)

    nawallet_records = load_nawallet_records(cursor)

    icost_rows = []
    for record in nawallet_records:
        row = ICostRow(
            date=datetime.datetime.fromtimestamp(record.time / 1000)
            .strftime("%Y年%m月%d日 %H:%M:%S".encode("unicode-escape").decode())
            .encode()
            .decode("unicode-escape"),
            type=nawallet_record_types[record.record_type_id][1] == 0
            and "支出"
            or "收入",
            amount=record.money / 100,
            category=RECORD_TYPE_MAP[record.record_type_id][0],
            subcategory=RECORD_TYPE_MAP[record.record_type_id][1],
            account_1=ASSETS_MAP[record.assets_id],
            account_2="",
            note=record.remark,
            currency="CNY",
            tags="",
        )
        icost_rows.append(row)

    save_icost_rows(icost_rows, OUTPUT_ICOST_IMPORT_FILE_PATH)


if __name__ == "__main__":
    main()
