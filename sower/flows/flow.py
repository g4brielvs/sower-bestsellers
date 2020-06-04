import os
import json
from datetime import datetime, timedelta

import pandas as pd
import prefect
import requests

from prefect import task, Flow, Parameter
from prefect.schedules import Schedule
from prefect.schedules.clocks import CronClock
from prefect.tasks.gcp.storage import GCSUpload
from prefect.tasks.notifications.email_task import EmailTask

from scrapy.crawler import CrawlerProcess

from sower.spiders.books import BooksSpider
from sower.settings import (
    credentials,
    FEED_FORMAT,
    FEED_URI,
    BUCKET,
    BUCKET_BESTSELLERS,
    BOOKSELLERS_LISTS,
    NYT_API_KEY,
    EMAIL_TO,
)


@task
def crawl():
    c = CrawlerProcess(
        {"USER_AGENT": "Mozilla/5.0", "FEED_FORMAT": FEED_FORMAT, "FEED_URI": FEED_URI,}
    )
    c.crawl(BooksSpider)
    c.start()


@task
def read():
    logger = prefect.context.get("logger")
    start_time = prefect.context.get("scheduled_start_time")

    try:
        df = pd.read_csv(FEED_URI)
        df["isbn13"] = df["link"].apply(lambda x: x.split("/")[-1])

        data = df.to_csv(index=False)
        blob = start_time.strftime("%Y%m%d%H%M%S") + ".csv"
        obj = GCSUpload(bucket=BUCKET).run(
            data=data, blob=blob, credentials=credentials,
        )
        logger.debug(f"Created {obj}")
    finally:
        os.remove(FEED_URI)

    return df


@task(max_retries=3, retry_delay=timedelta(seconds=60))
def get(name):
    BASE_URL = "https://api.nytimes.com"
    API_URL = "/svc/books/v3"
    API_METHOD = f"/lists/current/{name}.json"

    url = f"{BASE_URL}{API_URL}{API_METHOD}?api-key={NYT_API_KEY}"
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


@task(max_retries=3, retry_delay=timedelta(seconds=5))
def upload(data):
    logger = prefect.context.get("logger")

    results = data["results"]
    obj = GCSUpload(bucket=BUCKET_BESTSELLERS).run(
        data=json.dumps(data),
        blob=f"{results['list_name_encoded']}/{results['published_date']}.json",
        credentials=credentials,
    )
    logger.debug(f"Created {obj}")


@task
def create(data, bestseller_lists):

    columns = [
        "rank",
        "weeks_on_list",
        "title",
        "author",
        "publisher",
        "primary_isbn13",
    ]

    dataframes = []
    for bl in bestseller_lists:
        books = bl["results"]["books"]
        books = [{k: v for (k, v) in b.items() if k in columns} for b in books]
        df = pd.DataFrame(books)

        df["bestsellers_list"] = bl["results"]["list_name_encoded"]
        df["bestsellers_date"] = bl["results"]["bestsellers_date"]
        df["published_date"] = bl["results"]["published_date"]

        dataframes.append(df)

    df = pd.merge(
        pd.concat(dataframes),
        data,
        left_on="primary_isbn13",
        right_on="isbn13",
        how="inner",
        suffixes=("", "_y"),
    )
    return df[
        [
            "bestsellers_list",
            "bestsellers_date",
            "published_date",
            "rank",
            "weeks_on_list",
            "publisher",
            "author",
            "title",
            "isbn13",
            "link",
        ]
    ]


@task
def export(data):
    logger = prefect.context.get("logger")
    start_time = prefect.context.get("scheduled_start_time")

    try:
        filename = "data.xlsx"
        data.to_excel(filename, index=False)

        with open(filename, "rb") as f:
            data = f.read()
        blob = start_time.strftime("%Y%m%d%H%M%S") + ".xlsx"

        obj = GCSUpload(bucket=BUCKET).run(
            data=data, blob=blob, credentials=credentials
        )
        logger.debug(f"Created {obj}")

        return obj
    finally:
        os.remove(filename)


@task
def email(message):

    msg = f"""Dear colleague, 

        The New York Times updated its weekly best sellers lists and you can take a look at ranked Simon & Schuster books on them.

        Follow the link:
        https://storage.googleapis.com/sower/{message}


        Keep reading,

        --
        Sower Bestsellers
        """
    e = EmailTask(
        subject="Sower Bestsellers",
        msg=msg,
        smtp_server="smtp.gmail.com",
        smtp_port=465,
        smtp_type="SSL",
    )
    e.run(email_to="sower@g4brielvs.me")
    e.run(email_to=EMAIL_TO)


## create schedule for the Flow
schedule = Schedule(clocks=[CronClock("0 4 * * THU")])

with Flow("Sower Bestsellers", schedule) as flow:

    archive = read(upstream_tasks=[crawl])
    lists = get.map(BOOKSELLERS_LISTS)
    upload.map(lists)

    # create and merge
    df = create(archive, lists)
    fn = export(df)

    # notify
    email(fn)

flow.register()
