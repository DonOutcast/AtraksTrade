import csv
import logging
from io import StringIO
import pandas
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
        df: pandas.DataFrame | None = None,
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


def prepare_df(csv_texts: list[str]) -> pandas.DataFrame:
    frames = []
    for text in csv_texts:
        df_part = pandas.read_csv(
            StringIO(text),
            delimiter=";",
            header=0,
            engine="python",
            on_bad_lines="skip",
        )
        frames.append(df_part)

    df = pandas.concat(frames, ignore_index=True)

    df = df.rename(columns={
        "АВС/ DEF": "code",
        "От": "begin",
        "До": "end",
        "Оператор": "operator",
        "Регион": "region",
    })

    df = df[["code", "begin", "end", "operator", "region"]]
    df["region"] = df["region"].astype(str).apply(lambda s: s.split("|")[-1].strip())
    df["code"] = df["code"].astype(str).str.strip()
    df["begin"] = df["begin"].astype(str).str.strip()
    df["end"] = df["end"].astype(str).str.strip()

    df["begin"] = (df["code"] + df["begin"])
    df["end"] = (df["code"] + df["end"])
    df = df[df["begin"].str.isdigit() & df["end"].str.isdigit()]
    return df


def update_df_and_model(df: pandas.DataFrame, Model, column: str) -> None:
    existing = Model.objects.values_list("name", "id")
    name_to_id = dict(existing)

    new_names = [
        [name] for name in df[column].unique()
        if name not in name_to_id
    ]

    if new_names:
        logger.info("Found %s new %s entries, importing...", len(new_names), column)
        s_buf = write_string_io(columns=["name"], values=new_names)
        Model.objects.bulk_create(
            [Model(name=row[0]) for row in new_names],
            ignore_conflicts=True,
        )
        name_to_id = dict(Model.objects.values_list("name", "id"))

    df[column] = df[column].map(name_to_id)


def update_info() -> None:
    logger.info("Updating Rossvyaz data from opendata.digital.gov.ru")

    csv_file = fetch_all_csvs()
    df = prepare_df(csv_file)

    update_df_and_model(df, Operator, "operator")
    update_df_and_model(df, Region, "region")

    df["begin"] = df["begin"].astype("int64")
    df["end"] = df["end"].astype("int64")

    Phone.objects.all().delete()
    Phone.objects.bulk_create(
        [
            Phone(
                begin=row["begin"],
                end=row["end"],
                operator_id=row["operator"],
                region_id=row["region"],
            )
            for _, row in df.iterrows()
        ],
        batch_size=5000,
    )

    logger.info("Rossvyaz data successfully updated")


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
