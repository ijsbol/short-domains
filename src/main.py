import datetime
import json
import re
import string
import itertools
from typing import Callable, Final

import requests


VALID_DOMAIN_NAME_REGEX: Final[str] = r"[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}"


is_valid_domain: Callable[[str], bool] = lambda s: bool(re.search(VALID_DOMAIN_NAME_REGEX, s))


def generate_strings_to_check(size: int) -> list[str]:
    """Generate all possible x-length domain combinations."""
    letters = string.ascii_lowercase + string.digits
    return [
        ''.join(s) for s in itertools.product(letters, repeat=size)
        if is_valid_domain(''.join(s))
    ]


def check_domain_registration(domain_name: str, tld: str) -> bool | None:
    domain = f"{domain_name}.{tld}"
    with requests.get(f"https://pubapi-dot-domain-registry.appspot.com/whois/{domain}") as req:
        if req.status_code == 404:
            return False
        if req.status_code > 200:
            return None
        return True


def load_tld_registration_information(tld: str, size: int) -> None:
    time_start = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
    domains_to_check: list[str] = generate_strings_to_check(size)
    number_of_domains_to_check: int = len(domains_to_check)
    checked_domains: dict[str, bool | None | int] = {}
    for index, domain in enumerate(domains_to_check):
        print(f"> [{index+1}/{number_of_domains_to_check}] Checking {domain}.{tld}")
        registered = check_domain_registration(domain, tld)
        if registered is None:
            print(f"> [{index+1}/{number_of_domains_to_check}] {domain}.{tld} Lookup failed")
        else:
            print(f"> [{index+1}/{number_of_domains_to_check}] {domain}.{tld} is{[' not', ''][registered]} registered.")
        checked_domains[domain] = registered

        if index % 10 == 0:
            print("Saving progress...")
            checked_domains["___last_updated___"] = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
            with open(f"_data/json/{tld}-{size}.json", "w+") as f:
                json.dump(
                    obj=checked_domains,
                    fp=f,
                    indent=2,
                    ensure_ascii=True,
                )

    time_end = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

    checked_domains["___last_updated___"] = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())
    with open(f"_data/json/{tld}-{size}.json", "w+") as f:
        json.dump(
            obj=checked_domains,
            fp=f,
            indent=2,
            ensure_ascii=True,
        )

    registered_count = sum([1 for _, v in checked_domains.items() if v == True])
    unregistered_count = sum([1 for _, v in checked_domains.items() if v == False])
    failed_lookup_count = sum([1 for _, v in checked_domains.items() if v == None])
    successful_lookup_count = registered_count + unregistered_count
    total_count = registered_count + unregistered_count + failed_lookup_count
    success_rate = round((successful_lookup_count / total_count) * 100, 2)
    if success_rate > 99.999:
        success_rate = int(100)

    print(
        f"Fetched registration information for {total_count} domains."
        + f"\n  - Attempted: {number_of_domains_to_check}"
        + f"\n  - Failed: {failed_lookup_count}"
        + f"\n  - Lookup success rate: {success_rate}%"
        + f"\n  - {registered_count} registered"
        + f"\n  - {unregistered_count} unregistered"
        + f"\nTime taken: {round(time_end-time_start)} seconds."
    )


def main() -> None:
    with open("_data/config/tracked_tlds.json", "r") as f:
        config = json.load(f)
    for domain, lengths in config.items():
        for length in lengths:
            load_tld_registration_information(domain, length)


if __name__ == "__main__":
    main()
