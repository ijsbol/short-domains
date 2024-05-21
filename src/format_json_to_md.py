from collections import defaultdict
from datetime import datetime, timezone
import json
import glob
import pathlib
from typing import Callable, Final, TypedDict

from constants import LAST_UPDATED_KEY, DomainStatus


EMOJIS: Final[dict[int, str]] = {
    DomainStatus.UNREGISTERED.value: ':white_check_mark:',
    DomainStatus.AVAILABLE_FOR_APPLICATION.value: ':writing_hand:',
    DomainStatus.PREMIUM.value: ':gem:',
}
format_domain: Callable[[str, str, int], str] = lambda d, t, r: f'|{EMOJIS[r]}|`{d}.{t}`|'


class RawStats(TypedDict):
    tlds_tracked: set[str]
    failed_lookups: int
    domains_tracked: int
    premium_domains: int
    available_for_application: int
    available_domains_2l: int
    registration_rate_2l: list[float]


class StatsFormatted(TypedDict):
    tlds_tracked: int
    failed_lookups: int
    domains_tracked: int
    premium_domains: int
    available_for_application: int
    available_domains_2l: int
    registration_rate_2l: str
    data_formatted: str


def format_data_to_md(domain_data: dict[str, int], tld: str, length: int) -> str | None:
    updated_at = datetime.fromtimestamp(
        timestamp=int(domain_data[LAST_UPDATED_KEY] or 0),
        tz=timezone.utc,
    )
    updated_at_str = updated_at.strftime("%m/%d/%Y, %H:%M:%S")

    del domain_data[LAST_UPDATED_KEY]
    registered_count = sum([1 for _, v in domain_data.items() if v == DomainStatus.REGISTERED.value])
    premium_count = sum([1 for _, v in domain_data.items() if v == DomainStatus.PREMIUM.value])
    available_for_application_count = sum([1 for _, v in domain_data.items() if v == DomainStatus.AVAILABLE_FOR_APPLICATION.value])
    unregistered_count = sum([1 for _, v in domain_data.items() if v == DomainStatus.UNREGISTERED.value])
    unregistered_count += premium_count
    unregistered_count += available_for_application_count
    failed_lookup_count = sum([1 for _, v in domain_data.items() if v == DomainStatus.FAILED.value])
    successful_lookup_count = registered_count + unregistered_count
    if successful_lookup_count == 0:
        return None

    total_count = registered_count + unregistered_count + failed_lookup_count
    success_rate = round((successful_lookup_count / total_count) * 100, 2)
    registration_rate = round((registered_count / successful_lookup_count) * 100, 2)
    success_rate = int(100) if success_rate > 99.999 else success_rate
    registration_rate = int(100) if registration_rate > 99.999 else registration_rate

    unregistered_domains: list[tuple[str, int]] = [
        (domain, registered) for domain, registered in domain_data.items()
        if registered in [
            DomainStatus.UNREGISTERED.value,
            DomainStatus.PREMIUM.value,
            DomainStatus.AVAILABLE_FOR_APPLICATION.value,
        ]
    ]

    output = f"# Available {length} character long domains for `.{tld}`"
    output += f"\n\n## Data last updated: {updated_at_str}"
    output += f"\n\n|Stat|Amount|"
    output += f"\n|--|--|"
    output += f"\n|Registered domains|{registered_count}|"
    output += f"\n|Unregistered domains|{unregistered_count}|"
    output += f"\n|Premium domains|{premium_count}|"
    output += f"\n|Application only domains|{available_for_application_count}|"
    output += f"\n|Registration rate|{registration_rate}%|"
    output += f"\n|Failed lookups|{failed_lookup_count}|"
    output += f"\n|Successful lookups|{successful_lookup_count}|"
    output += f"\n|Lookup success rate|{success_rate}%|"
    output += f"\n"

    starts_with_sections: dict[str, list[tuple[str, int]]] = defaultdict(lambda: [])
    for domain, registration in unregistered_domains:
        starts_with_char = domain[0]
        starts_with_sections[starts_with_char].append((domain, registration))

    output += f"\n\n|Meaning|Emoji|"
    output += f"\n|--|--|"
    output += f"\n|Unregistered|{EMOJIS[DomainStatus.UNREGISTERED.value]}|"
    output += f"\n|Application only|{EMOJIS[DomainStatus.AVAILABLE_FOR_APPLICATION.value]}|"
    output += f"\n|Premium domain|{EMOJIS[DomainStatus.PREMIUM.value]}|"
    output += f"\n"

    for starts_with_section, domains in starts_with_sections.items():
        registration_data_formatted = '\n'.join([format_domain(domain, tld, registration) for domain, registration in domains])
        output += f"\n<details>\n<summary>{len(domains)} unregistered domains starting with <bold><code>{starts_with_section}</code></bold></summary>"
        output += f"\n\n|Type|Domain|"
        output += f"\n|--|--|"
        output += f"\n{registration_data_formatted}"
        output += "\n</details>"
    return output


def main() -> None:
    json_data_files = glob.glob("_data/json/*.json")
    raw_stats: RawStats = {
        "tlds_tracked": set(),
        "failed_lookups": 0,
        "domains_tracked": 0,
        "premium_domains": 0,
        "available_for_application": 0,
        "available_domains_2l": 0,
        "registration_rate_2l": [],
    }
    data_formatted = ""

    for raw_file_path in json_data_files:
        file_path = pathlib.Path(raw_file_path)
        with open(file_path, "r") as fr:
            domain_json_data = json.load(fr)

        raw_file_name = file_path.name.removesuffix(".json")
        tld = raw_file_name.split("-")[0]
        length = int(raw_file_name.split("-")[1])

        raw_stats["tlds_tracked"].add(tld)

        formatted_text = format_data_to_md(
            domain_data=domain_json_data,
            tld=tld,
            length=length,
        )

        if formatted_text is None:
            continue

        registered_count = sum([1 for _, v in domain_json_data.items() if v == DomainStatus.REGISTERED.value])
        premium_count = sum([1 for _, v in domain_json_data.items() if v == DomainStatus.PREMIUM.value])
        available_for_application_count = sum([1 for _, v in domain_json_data.items() if v == DomainStatus.AVAILABLE_FOR_APPLICATION.value])
        unregistered_count = sum([1 for _, v in domain_json_data.items() if v == DomainStatus.UNREGISTERED.value])
        unregistered_count += premium_count
        unregistered_count += available_for_application_count
        failed_lookup_count = sum([1 for _, v in domain_json_data.items() if v == DomainStatus.FAILED.value])

        successful_lookup_count = registered_count + unregistered_count
        total_count = successful_lookup_count + failed_lookup_count
        success_rate = round((successful_lookup_count / total_count) * 100, 2)
        registration_rate = round((registered_count / successful_lookup_count) * 100, 2)
        success_rate = int(100) if success_rate > 99.999 else success_rate
        registration_rate = int(100) if registration_rate > 99.999 else registration_rate

        data_formatted += (
            f"\n#### [{unregistered_count} available <bold>{length} character long <code>.{tld}</code> domains</bold>]"
            + f"(https://github.com/Isabe1le/domain-registration-tracking/blob/main/out/{tld}-{length}-long-domains.md)"
            + f"\n"
        )

        raw_stats["domains_tracked"] += successful_lookup_count
        raw_stats["failed_lookups"] += failed_lookup_count
        raw_stats["premium_domains"] += premium_count
        raw_stats["available_for_application"] += available_for_application_count
        if length == 2:
            raw_stats["available_domains_2l"] += unregistered_count
            raw_stats["registration_rate_2l"].append(registration_rate)

        with open(f"out/{tld}-{length}-long-domains.md", "w+") as fw:
            fw.write(formatted_text)

    registration_rate_2l = sum(raw_stats["registration_rate_2l"]) / len(raw_stats["registration_rate_2l"])
    registration_rate_2l = int(100) if registration_rate_2l > 99.999 else registration_rate
    registration_rate_2l = f"{registration_rate_2l}%"
    stats_formatted: StatsFormatted = {
        "available_domains_2l": raw_stats["available_domains_2l"],
        "failed_lookups": raw_stats["failed_lookups"],
        "domains_tracked": raw_stats["domains_tracked"],
        "premium_domains": raw_stats["premium_domains"],
        "available_for_application": raw_stats["available_for_application"],
        "tlds_tracked": len(raw_stats["tlds_tracked"]),
        "registration_rate_2l": registration_rate_2l,
        "data_formatted": data_formatted,
    }

    with open(f"README.md", "w") as readme_f:
        with open(f"_data/README.md.template", "r") as template_f:
            template = template_f.read()
        print(template)
        readme_f.write(template % stats_formatted)


if __name__ == "__main__":
    main()
