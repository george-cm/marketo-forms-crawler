"""Explore AEM events search API."""
import requests


def main():
    """Main function."""
    payload = {
        "query": "",
        "filters": {"all": [{"document_type": ["events"]}, {"language": "en_us"}]},
        "facets": {
            "article_tags": {"type": "value", "size": 250},
            "location": {"type": "value", "size": 250},
            "tags": {"type": "value", "size": 250},
        },
        "sort": [{"start_date": "desc"}],
        "page": {"current": 1, "size": 50},
    }
    headers = {
        "authority": "sps.honeywell.com",
        "method": "POST",
        "path": "/pif/api/search/v1/joule-bt-sps-sps-prod/search?appId: 81",
        "scheme": "https",
        "accept": "application/json, text/javascript, */*; q: 0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en-GB;q=0.9,en;q=0.8,ro;q=0.7,es;q: 0.6",
        "cache-control": "no-cache",
        "csrf-token": "undefined",
        "dnt": "1",
        "origin": "https://sps.honeywell.com",
        "pragma": "no-cache",
        "referer": "https://sps.honeywell.com/us/en/events",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v: "120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest",
    }

    with requests.Session() as sess:
        response = sess.post(
            "https://sps.honeywell.com/pif/api/search/v1/joule-bt-sps-sps-prod/search?appId=81",
            json=payload,
            headers=headers,
        )
        print(response.json())


if __name__ == "__main__":
    main()
