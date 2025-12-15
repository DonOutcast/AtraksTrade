import re
import csv
import logging
from io import StringIO
import pandas as pd
import phonenumbers
import requests

from .exceptions import NumberNotRecognized, NumberNotFound
from .models import Region, Operator, Phone

from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

CSV_URLS = [
    "https://opendata.digital.gov.ru/downloads/ABC-3xx.csv?1765775329112",
    "https://opendata.digital.gov.ru/downloads/ABC-4xx.csv?1765775329113",
    "https://opendata.digital.gov.ru/downloads/ABC-8xx.csv?1765775329114",
    "https://opendata.digital.gov.ru/downloads/DEF-9xx.csv?1765775329114",
]


def get_user_agent() -> str:
    try:
        ua = UserAgent()
        return ua.random
    except Exception:
        return (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )


def write_string_io(
        df: pd.DataFrame | None = None,
        columns=None,
        values=None,
) -> StringIO:
    if df is not None:
        if columns is None:
            columns = df.columns
        if values is None:
            values = df.values

    if columns is None or values is None:
        raise ValueError("Нужно передать либо df, либо columns и values")

    s_buf = StringIO()
    writer = csv.writer(s_buf)
    writer.writerow(columns)
    writer.writerows(values)
    s_buf.seek(0)
    return s_buf


def fetch_csv(url: str) -> bytes:
    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "text/csv,application/octet-stream,*/*;q=0.8",
        "Referer": "https://opendata.digital.gov.ru/",
    }
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        raise ConnectionError(f"{url} not downloaded correctly: {resp.status_code}")
    return resp.content


def fetch_all_csvs() -> list[str]:
    logger.info("Fetching CSV files from opendata.digital.gov.ru")

    texts = []
    for url in CSV_URLS:
        content = fetch_csv(url)
        texts.append(content.decode("utf-8-sig", errors="replace"))
    return texts


def prepare_df(csv_file) -> pd.DataFrame:
    df = pd.read_csv(
        csv_file,
        delimiter=";",
        header=None,
        dtype=str,
        engine="python",
        on_bad_lines="skip",
    )

    df = df.iloc[:, :6]
    df.columns = ["code", "begin", "end", "count", "operator", "region"]

    for col in ["code", "begin", "end", "operator", "region"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df = df[df["begin"].str.fullmatch(r"\d+")]
    df = df[df["end"].str.fullmatch(r"\d+")]
    df = df[df["code"].str.fullmatch(r"\d+")]
    df["begin"] = df["code"] + df["begin"]
    df["end"] = df["code"] + df["end"]
    df = df[(df["operator"] != "") & (df["region"] != "")]
    m = df["region"].str.startswith("Московская область", na=False)
    df.loc[m, "region"] = "г. Москва и Московская область"
    df["begin"] = df["begin"].astype("int64")
    df["end"] = df["end"].astype("int64")

    return df[["begin", "end", "operator", "region"]]


def _norm_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def update_df_and_model(df: pd.DataFrame, Model, column: str) -> None:
    raw_col = f"__{column}_raw"
    df[raw_col] = df[column].apply(_norm_text)

    df = df[df[raw_col] != ""]
    df[column] = df[raw_col]

    existing = set(Model.objects.values_list("name", flat=True))
    to_create = [Model(name=name) for name in df[column].unique() if name not in existing]
    if to_create:
        Model.objects.bulk_create(to_create, ignore_conflicts=True)

    name_to_id = dict(Model.objects.values_list("name", "id"))
    df[column] = df[column].map(name_to_id)

    if df[column].isna().any():
        bad_names = df.loc[df[column].isna(), raw_col].unique().tolist()

        for name in bad_names:
            Model.objects.get_or_create(name=name)

        name_to_id = dict(Model.objects.values_list("name", "id"))
        df[column] = df[raw_col].map(name_to_id)

    bad = df[df[column].isna()]
    if not bad.empty:
        sample = bad[["begin", "end", "operator", raw_col]].head(10)
        raise ValueError(f"Не удалось замапить {column} в id. Пример строк:\n{sample}")

    return df.drop(columns=[raw_col])


def bulk_insert_phones(df, batch_size=50000):
    objs = []
    for row in df.itertuples(index=False):
        objs.append(
            Phone(
                begin=int(row.begin),
                end=int(row.end),
                operator_id=int(row.operator),
                region_id=int(row.region),
            )
        )
        if len(objs) >= batch_size:
            Phone.objects.bulk_create(objs, batch_size=batch_size)
            objs.clear()

    if objs:
        Phone.objects.bulk_create(objs, batch_size=batch_size)


def update_info() -> None:
    logger.info("Starting Rossvyaz update...")
    Phone.objects.all().delete()
    for url in CSV_URLS:
        logger.info("Downloading: %s", url)
        content = fetch_csv(url)
        df = prepare_df(StringIO(content.decode("utf-8", errors="ignore")))
        df = update_df_and_model(df, Operator, "operator")
        df = update_df_and_model(df, Region, "region")
        df = df.dropna(subset=["operator", "region"])
        df["operator"] = df["operator"].astype("int64")
        df["region"] = df["region"].astype("int64")
        bulk_insert_phones(df[["begin", "end", "operator", "region"]])

    logger.info("Rossvyaz update finished.")



def parse_num(num: str) -> phonenumbers.PhoneNumber:
    try:
        parsed = phonenumbers.parse(num, "RU")
    except phonenumbers.NumberParseException:
        raise NumberNotRecognized(num)

    if not phonenumbers.is_valid_number(parsed):
        raise NumberNotRecognized(num)

    return parsed


def get_num_info(num: str) -> dict:
    parsed = parse_num(num)
    num_str = str(parsed.national_number)

    if len(num_str) != 10:
        raise NumberNotFound(num_str)

    num_int = int(num_str)
    num_info = Phone.find(num_int)

    if num_info is None:
        raise NumberNotFound(num_str)

    return {
        "number": "7" + num_str,
        "operator": num_info.operator.name,
        "region": num_info.region.name,
    }
