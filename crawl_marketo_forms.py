"""Crawl links from a sitemap.xml url and extract Marketo form ids."""
import argparse
import logging
from pathlib import Path

import scrapy.core.scraper
import scrapy.utils.misc
from scrapy.crawler import CrawlerProcess
from scrapy.selector import SelectorList
from scrapy.spiders import SitemapSpider
from scrapy.utils.url import parse_url

__version__ = "0.5.0"


# pylint: disable-next=W0622:redefined-builtin,W0613:unused-argument
def warn_on_generator_with_return_value_stub(spider, callable):
    """Stub for scrapy.utils.misc.warn_on_generator_with_return_value."""
    pass  # pylint: disable=W0107:unnecessary-pass


scrapy.utils.misc.warn_on_generator_with_return_value = (
    warn_on_generator_with_return_value_stub
)
scrapy.core.scraper.warn_on_generator_with_return_value = (
    warn_on_generator_with_return_value_stub
)


class MySpider(SitemapSpider):
    """Spider class for crawling Marketo forms from a sitemap url."""

    name = "tagforms"
    allowed_domains: list[str] = []
    sitemap_urls: list[str] = []
    custom_settings = {
        "AUTOTHROTTLE_ENABLED": True,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
    }

    def parse(self, response, **kwargs):
        formloads: list[str] = response.xpath(
            "//script[contains(., 'MktoForms2.loadForm(')]/text()"
        ).re(r"MktoForms2.loadForm\((.*?)\)")
        if len(formloads) > 0:
            for formload in formloads:  # type: ignore
                details: list = [x.strip().strip('"') for x in formload.split(",")]
                yield {
                    "url": response.url,
                    "form_id": details[2],
                    "Marketo_domain": details[0].strip("/"),
                    "munchkin_id": details[1],
                }
        else:
            mkto_domains_urls = response.xpath(
                "//link[contains(@href, 'marketo.com/js/forms2/js/forms2')] | "
                "//script[contains(@src, 'marketo.com/js/forms2/js/forms2')]"
            )
            if mkto_domains_urls:
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
                        "form_id": form_id.split("_")[1],
                        "Marketo_domain": "; ".join(mkto_domains),
                        "munchkin_id": "; ".join(munchkin_ids),
                    }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        prog="crawl_marketo_forms",
        description=__doc__,
    )
    parser.add_argument("url", help="URL of sitemap")
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
        type=int,
        dest="athrottlemaxdelay",
        help="set the maximum delay between requests. Default is 60.",
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
    MySpider.sitemap_urls = [args.url]
    domain = parse_url(args.url).hostname
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
