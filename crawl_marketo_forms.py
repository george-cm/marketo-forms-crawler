"""Crawl links from a site's url and extract Marketo form ids."""

import argparse
import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import scrapy.core.scraper
import scrapy.utils.misc
from scrapy import Spider
from scrapy.crawler import CrawlerProcess
from scrapy.http import JsonRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import SelectorList
from scrapy.utils.url import ParseResult, parse_url

__version__ = "0.9.0"


# pylint: disable-next=W0622:redefined-builtin,W0613:unused-argument
def warn_on_generator_with_return_value_stub(spider, callable) -> None:
    """Stub for scrapy.utils.misc.warn_on_generator_with_return_value."""
    pass  # pylint: disable=W0107:unnecessary-pass


scrapy.utils.misc.warn_on_generator_with_return_value = (
    warn_on_generator_with_return_value_stub
)
scrapy.core.scraper.warn_on_generator_with_return_value = (
    warn_on_generator_with_return_value_stub
)


class MySpider(Spider):
    """Spider class for crawling Marketo forms from a site's url."""

    name = "tagforms"
    allowed_domains: List[str] = []
    start_urls: List[str] = []
    linkextractor: LinkExtractor  # = LinkExtractor(allow="/en-gb/")
    custom_settings = {
        "AUTOTHROTTLE_ENABLED": True,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "HTTPERROR_ALLOWED_CODES": [404],
    }

    def parse(
        self, response, **kwargs
    ) -> Generator[dict[str, Any], Any, None] | Generator[scrapy.Request, None, None]:
        if response.status == 404:
            logging.warning("Page not found: %s", response.url)
            yield {
                "url": response.url,
                "status": response.status,
                "error": "Page not found",
                "form_id": None,
                "Marketo_domain": None,
                "munchkin_id": None,
                "program_name": None,
                "title": None,
                "meta description": None,
                "h1 (heading 1)": None,
                "from_experience_fragment": None,
            }
        elif response.url.strip("/").endswith("https://sps.honeywell.com/us/en/events"):
            items_per_page = 1
            yield JsonRequest(
                "https://sps.honeywell.com/pif/api/search/v1/joule-bt-sps-sps-prod/search?appId=81",
                callback=self.parse_events,
                method="POST",
                data={
                    "query": "",
                    "filters": {
                        "all": [{"document_type": ["events"]}, {"language": "en_us"}]
                    },
                    "facets": {
                        "article_tags": {"type": "value", "size": 250},
                        "location": {"type": "value", "size": 250},
                        "tags": {"type": "value", "size": 250},
                    },
                    "sort": [{"start_date": "desc"}],
                    "page": {"current": 1, "size": items_per_page},
                },
            )
        else:
            page_details: Dict[str, Any]
            formloads: List[str] = response.xpath(
                "//script[contains(., 'MktoForms2.loadForm(')]/text()"
            ).re(r"MktoForms2.loadForm\((.*?)\)")

            if len(formloads) > 0:
                for formload in formloads:  # type: ignore
                    details: List = [x.strip().strip('"') for x in formload.split(",")]
                    page_details = self._extract_page_details(response)
                    yield {
                        "url": response.url,
                        "status": response.status,
                        "error": None,
                        "form_id": int(details[2]),
                        "Marketo_domain": details[0].strip("/"),
                        "munchkin_id": details[1],
                        **page_details,
                        "from_experience_fragment": None,
                    }
            else:
                mkto_domains_urls = response.xpath(
                    "//link[contains(@href, 'marketo.com/js/forms2/js/forms2')] | "
                    "//script[contains(@src, 'marketo.com/js/forms2/js/forms2')]"
                )
                if mkto_domains_urls:
                    page_details = self._extract_page_details(response)
                    mkto_domains = []
                    for mkto_domain in mkto_domains_urls:  # type: ignore
                        if mkto_domain.attrib.get("href"):
                            url = mkto_domain.attrib["href"]
                        elif mkto_domain.attrib.get("src"):
                            url = mkto_domain.attrib["src"]
                        else:
                            continue
                        mkto_domain = parse_url(url).hostname
                        mkto_domains.append(mkto_domain)
                    mkto_domains = list(set(mkto_domains))
                    munchkin_ids = response.xpath(
                        "//script[contains(text(), 'Munchkin.init(')]/text()"
                    ).re(r"Munchkin.init\((.*?)\)")
                    munchkin_ids = list(
                        {x.strip().strip("'").strip('"') for x in munchkin_ids}  # type: ignore
                    )
                    marketo_form_ids: SelectorList = response.xpath(
                        "//form[starts-with(@id, 'mktoForm_')]/@id"
                    ).getall()
                    for form_id in marketo_form_ids:  # type: ignore
                        yield {
                            "url": response.url,
                            "status": response.status,
                            "error": None,
                            "form_id": int(form_id.split("_")[1]),  # type: ignore
                            "Marketo_domain": "; ".join(mkto_domains),
                            "munchkin_id": "; ".join(munchkin_ids),
                            **page_details,
                            "from_experience_fragment": None,
                        }
        experience_fragments = response.xpath(
            "//a[@data-target='#cta-modal'][@data-modal]/@data-modal"
        ).getall()
        if len(experience_fragments) > 0:
            logging.info("Found experience fragments: %s", response.url)
            for link in experience_fragments:  # type: ignore
                experience_fragment_url = (
                    link.strip("/") + "/jcr:content/root/responsivegrid.html"
                )
                parsed_url = parse_url(response.url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                yield response.follow(
                    f"{base_url}/{experience_fragment_url}",
                    callback=self.parse_experience_fragments,
                    meta={
                        "referer": response.url,
                        "page_details": self._extract_page_details(response),
                        "response_status": response.status,
                    },
                    dont_filter=True,
                )
        for link in self.linkextractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse)

    def parse_events(self, response):
        """Parse events from the search API"""
        items_per_page = (
            response.json().get("meta", {}).get("page", {}).get("total_results", 0)
        )
        if items_per_page > 0:
            yield JsonRequest(
                "https://sps.honeywell.com/pif/api/search/v1/joule-bt-sps-sps-prod/search?appId=81",
                callback=self.parse_all_events,
                method="POST",
                data={
                    "query": "",
                    "filters": {
                        "all": [{"document_type": ["events"]}, {"language": "en_us"}]
                    },
                    "facets": {
                        "article_tags": {"type": "value", "size": 250},
                        "location": {"type": "value", "size": 250},
                        "tags": {"type": "value", "size": 250},
                    },
                    "sort": [{"start_date": "desc"}],
                    "page": {"current": 1, "size": items_per_page},
                },
            )

    def parse_all_events(self, response):
        """Parse all events."""
        for event in response.json().get("results", []):
            yield scrapy.Request(
                event.get("url", {}).get("raw", None), callback=self.parse
            )

    def parse_experience_fragments(
        self, response
    ) -> Optional[Generator[dict[str, Any], Any, None]]:
        """Parse experience fragments."""
        logging.info(
            "Parsing experience fragments: %s, %s",
            response.url,
            response.meta.get("referer"),
        )
        found_on_page = response.meta.get("referer")

        formloads: List[str] = response.xpath(
            "//script[contains(., 'MktoForms2.loadForm(')]/text()"
        ).re(r"MktoForms2.loadForm\((.*?)\)")

        if len(formloads) > 0:
            for formload in formloads:  # type: ignore
                details: List = [x.strip().strip('"') for x in formload.split(",")]
                page_details = response.meta.get("page_details")
                yield {
                    "url": found_on_page,
                    "status": response.meta.get("response_status"),
                    "error": None,
                    "form_id": details[2],
                    "Marketo_domain": details[0].strip("/"),
                    "munchkin_id": details[1],
                    **page_details,
                    "from_experience_fragment": True,
                }
        return None

    def _extract_page_details(self, response) -> Dict[str, Any]:
        return {
            "program_name": response.xpath("//*[@id='ProgramName']/text()").get(),
            "title": response.xpath("//title/text()").get(),
            "meta description": response.xpath(
                "//meta[@name='description']/@content"
            ).get(),
            "h1 (heading 1)": " ".join(response.xpath("string(//h1)").get().split()),
        }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        prog="crawl_marketo_forms",
        description=__doc__,
    )
    parser.add_argument("url", help="URL of the site to crawl.")
    parser.add_argument("output", help="CSV output file.")
    parser.add_argument(
        "--append",
        "-a",
        action="store_true",
        help="append to CSV file. Otherwise, overwrite.",
    )
    parser.add_argument(
        "--version", "-V", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--noautothrottle",
        "-na",
        action="store_true",
        dest="noautothrottle",
        help="disable autothrottle. The software will crawl faster,"
        " but may be blocked by the website server.",
    )
    parser.add_argument(
        "--autothrottlemaxdelay",
        "-amd",
        type=float,
        dest="athrottlemaxdelay",
        help="set the maximum delay between requests in seconds. Default is 60s.",
    )
    parser.add_argument("--logfile", "-lf", help="log file")
    parser.add_argument(
        "--loglevel",
        "-ll",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="DEBUG",
        help="log level. Default: DEBUG",
    )
    parser.add_argument(
        "--logappend",
        "-la",
        action="store_true",
        help="append to log file instead of overwriting.",
    )
    args: argparse.Namespace = parser.parse_args()
    if not args.append:
        output = Path(args.output)
        if output.exists():
            output.unlink()
    process = CrawlerProcess(
        settings={
            "FEEDS": {
                args.output: {"format": "csv"},
            },
        }
    )

    logger: logging.Logger = logging.getLogger()
    logger.info(args.url)

    parsed_url: ParseResult = parse_url(args.url)
    restrict_path = parsed_url.path
    domain = parse_url(args.url).hostname

    MySpider.start_urls = [args.url]
    MySpider.linkextractor = LinkExtractor(allow=[f"/{restrict_path.strip('/')}/"])

    if domain is not None:
        MySpider.allowed_domains = [domain]

    if args.noautothrottle:
        MySpider.custom_settings["AUTOTHROTTLE_ENABLED"] = False  # type: ignore

    if args.athrottlemaxdelay:
        MySpider.custom_settings["AUTOTHROTTLE_MAX_DELAY"] = args.athrottlemaxdelay  # type: ignore

    if args.logfile:
        logfile = Path(args.logfile)
        if not logfile.parent.exists():
            logfile.parent.mkdir(parents=True)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        MySpider.custom_settings["LOG_ENABLED"] = True  # type: ignore
        MySpider.custom_settings["LOG_FILE"] = logfile  # type: ignore

        if args.logappend:
            MySpider.custom_settings["LOG_FILE_APPEND"] = True  # type: ignore
        else:
            MySpider.custom_settings["LOG_FILE_APPEND"] = False  # type: ignore

        MySpider.custom_settings["LOG_LEVEL"] = args.loglevel  # type: ignore

    process.crawl(MySpider)
    logger.info("Starting crawl")
    process.start()


if __name__ == "__main__":
    main()
