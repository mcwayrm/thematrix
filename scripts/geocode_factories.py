#!/usr/bin/env python3
"""
Script 2: Look up and geocode factory locations for a given company ticker.

Usage:
    python geocode_factories.py <ticker> --input factories.csv [--output output.csv]
    python geocode_factories.py <ticker> --search "Ford Motor" [--output output.csv]

Modes:
  --input   Provide a CSV with columns: facility_name, city, country
            (and optionally state_province). The script geocodes each row
            using OpenStreetMap Nominatim (free, no API key needed).

  --search  Provide a company name. The script searches for known
            manufacturing/factory locations and geocodes them.
            (Uses Nominatim search, results may need manual review.)

Rate limiting: Nominatim has a 1 request/second policy. The script
respects this automatically.
"""

import argparse
import csv
import os
import sys
import time
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


def geocode_from_csv(ticker, input_path, output_path):
    """Read a CSV of factory locations and geocode each row."""
    geolocator = Nominatim(user_agent="bloomberg_esg_factory_geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

    # Read input
    with open(input_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(f"No rows found in {input_path}")
        return

    # Determine which columns exist
    has_state = "state_province" in rows[0]
    has_products = "products" in rows[0]
    has_type = "facility_type" in rows[0]

    print(f"Geocoding {len(rows)} facilities for {ticker}...")
    results = []

    for i, row in enumerate(rows):
        name = row.get("facility_name", "").strip()
        city = row.get("city", "").strip()
        state = row.get("state_province", "").strip() if has_state else ""
        country = row.get("country", "").strip()

        # Build search query (city + state + country gives best results)
        query_parts = [p for p in [city, state, country] if p]
        query = ", ".join(query_parts)

        lat, lon = None, None
        try:
            location = geocode(query)
            if location:
                lat = round(location.latitude, 4)
                lon = round(location.longitude, 4)
                status = "OK"
            else:
                status = "NOT_FOUND"
        except Exception as e:
            status = f"ERROR: {e}"

        result = {
            "ticker": ticker,
            "facility_name": name,
            "city": city,
            "country": country,
            "latitude": lat,
            "longitude": lon,
            "geocode_status": status,
        }
        if has_state:
            result["state_province"] = state
        if has_type:
            result["facility_type"] = row.get("facility_type", "")
        if has_products:
            result["products"] = row.get("products", "")

        results.append(result)
        symbol = "+" if lat else "x"
        print(f"  [{symbol}] {name} ({city}, {country}) -> {lat}, {lon}")

    # Write output
    fields = ["ticker", "facility_name", "facility_type", "city",
              "state_province", "country", "latitude", "longitude",
              "products", "geocode_status"]
    # Only include fields that exist in the data
    fields = [f for f in fields if any(f in r for r in results)]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    ok = sum(1 for r in results if r["geocode_status"] == "OK")
    print(f"\nGeocoded {ok}/{len(results)} facilities. Saved to {output_path}")


def search_factories(ticker, company_name, output_path):
    """Search for factory/manufacturing locations for a company."""
    geolocator = Nominatim(user_agent="bloomberg_esg_factory_geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

    # Search for the company's factories/plants
    queries = [
        f"{company_name} factory",
        f"{company_name} plant",
        f"{company_name} manufacturing",
        f"{company_name} assembly",
    ]

    print(f"Searching for {company_name} factory locations...")
    results = []
    seen = set()

    for query in queries:
        try:
            locations = geolocator.geocode(query, exactly_one=False, limit=10)
            if locations:
                for loc in locations:
                    key = (round(loc.latitude, 2), round(loc.longitude, 2))
                    if key not in seen:
                        seen.add(key)
                        results.append({
                            "ticker": ticker,
                            "facility_name": loc.address[:80],
                            "city": "",
                            "country": "",
                            "latitude": round(loc.latitude, 4),
                            "longitude": round(loc.longitude, 4),
                            "geocode_status": "SEARCH",
                            "search_query": query,
                        })
                        print(f"  [+] {loc.address[:70]}")
        except Exception as e:
            print(f"  [x] Query '{query}' failed: {e}")
        time.sleep(1.1)

    if not results:
        print("No locations found. Try providing a CSV with --input instead.")
        return

    fields = ["ticker", "facility_name", "city", "country",
              "latitude", "longitude", "geocode_status", "search_query"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"\nFound {len(results)} locations. Saved to {output_path}")
    print("NOTE: Search results may include non-factory locations. Review and filter.")


def main():
    parser = argparse.ArgumentParser(
        description="Geocode factory locations for a company ticker"
    )
    parser.add_argument("ticker", help="Bloomberg ticker (e.g., 'F US')")
    parser.add_argument(
        "--input", "-i", default=None,
        help="CSV with columns: facility_name, city, country [, state_province, facility_type, products]"
    )
    parser.add_argument(
        "--search", "-s", default=None,
        help="Company name to search for factory locations (e.g., 'Ford Motor')"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output CSV path (default: <ticker>_factories_geocoded.csv)"
    )
    args = parser.parse_args()

    default_out = args.ticker.replace(" ", "_") + "_factories_geocoded.csv"
    output_path = args.output or default_out

    if args.input:
        geocode_from_csv(args.ticker, args.input, output_path)
    elif args.search:
        search_factories(args.ticker, args.search, output_path)
    else:
        print("Provide either --input <csv> or --search <company_name>")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
