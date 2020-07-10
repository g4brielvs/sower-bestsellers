# sower-bestsellers

The New York Times Best Sellers lists are published every. Every Thurdays at 04:00 UTC, `sower-bestsellers` run a spider to collect Simon & Schuster [catalog](https://www.simonandschuster.com/search/books), compares it to the best sellers lists and sends a email with the matches.

```
BOOKSELLERS_LISTS = [
    "advice-how-to-and-miscellaneous",
    "childrens-middle-grade-hardcover",
    "combined-print-and-e-book-fiction",
    "combined-print-and-e-book-nonfiction",
    "hardcover-fiction",
    "hardcover-nonfiction",
    "paperback-nonfiction",
    "picture-books",
    "series-books",
    "trade-fiction-paperback",
    "young-adult-hardcover",
    "audio-fiction",
    "audio-nonfiction",
    "business-books",
    "graphic-books-and-manga",
    "mass-market-monthly",
    "middle-grade-paperback-monthly",
    "young-adult-paperback-monthly",
]
```

## Set up

- Get API key from [New York Times](https://developers.nytimes.com)
- Create a [Google service account](https://cloud.google.com/compute/docs/access/service-accounts)

- Install [Docker](https://docs.docker.com/get-docker/)
- Install **Python3.7**
- Run ```pip install -r requirements```
- Fill out `.env`

## Run

```
source .env 

prefect server start

prefect agent start
```

Register the flow,

```python
python sower/flows/flow.py
```

Go to http://localhost:8080. Sit back and wait every week for the report on your email.

## Future

1. Dockerize
2. Use Slack instead of Email
3. MongoDB. This is something that I actually did, but I opted to use Google Cloud Storage
4. Use Simon & Schuster internal database. That would be quicker and future-proof in case the website changes.

## License

Copyright (c) 2020 Gabriel Stefanini Vicente

- Non Commercial: You may not use the material for commercial purposes.
- No Derivatives: You may not remix, transform, or build upon the material.