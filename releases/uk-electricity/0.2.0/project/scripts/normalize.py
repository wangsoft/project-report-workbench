"""Read official regional electricity tables without altering the source workbook."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from openpyxl import load_workbook

REGIONS = ['UK Total', 'England', 'Scotland', 'Wales', 'Northern Ireland']
LABELS = {'total': 'Total all generating companies', 'fossil': 'Fossil fuels',
          'nuclear': 'Nuclear', 'renewables': 'Renewables'}


def clean(value):
    return re.sub(r'\s*\[note[^]]*\]', '', str(value), flags=re.I).strip()


def normalize(path, year):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = book['Electricity generation by fuel']
        rows = list(sheet.iter_rows())
        header = next(row for row in rows if row[0].value == 'Generator type')
        positions = {}
        for c in header[2:]:
            if c.value is None:
                continue
            match = re.fullmatch(r'(\d{4}) (UK Total|England|Scotland|Wales|Northern Ireland)', str(c.value))
            if not match:
                raise ValueError(f'Unknown column header: {c.value}')
            key = (int(match[1]), match[2])
            if key in positions:
                raise ValueError(f'Duplicate year/region: {key}')
            positions[key] = c.column - 1
        all_years = sorted({k[0] for k in positions})
        if year != max(all_years):
            raise ValueError('Report year must equal workbook latest year; avoid unnoticed future-data exposure')
        selected = {}
        for metric, label in LABELS.items():
            matches = [row for row in rows if row[0].value == 'All generating companies'
                       and clean(row[1].value) == label]
            if len(matches) != 1:
                raise ValueError(f'Expected one row for {metric}')
            selected[metric] = matches[0]
        records = []
        for y in all_years:
            for region in REGIONS:
                if (y, region) not in positions:
                    raise ValueError(f'Missing region/year {y} {region}')
                column = positions[(y, region)]
                values, locators = {}, {}
                for metric, row in selected.items():
                    cell = row[column]
                    value = cell.value
                    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                        raise ValueError(f'Invalid or uncached numeric cell: {sheet.title}!{cell.coordinate}')
                    values[metric] = value
                    locators[metric] = f'{sheet.title}!{cell.coordinate}'
                if values['total'] <= 0:
                    raise ValueError('Total generation must be positive')
                records.append(dict(year=y, region=region, values=values, locators=locators))
        # Separate source table check. The published 2024 workbook has an England6 footnote typo.
        supply = list(book['Generation and supply'].iter_rows())
        supply_header = next(row for row in supply if row[0].value == 'Components of electricity generation and supply')
        supply_total = next(row for row in supply if row[0].value == 'Total electricity generated')
        supplied = {}
        for cell in supply_header[1:]:
            if cell.value:
                name = str(cell.value).replace('2022 England6', '2022 England')
                supplied[name] = supply_total[cell.column - 1].value
        cross_checks = []
        historical_gaps = []
        active_gaps = []
        for record in records:
            other = supplied.get(f'{record["year"]} {record["region"]}')
            if type(other) not in (int, float):
                raise ValueError('Missing cross-table generation total')
            gap = abs(other - record['values']['total'])
            detail = dict(year=record['year'], region=record['region'], gap_gwh=gap)
            if record['year'] >= year - 4:
                cross_checks.append(gap)
                if gap > 0.001: active_gaps.append(detail)
            elif gap > 0.001:
                historical_gaps.append(detail)
        return dict(schema_version=1, unit='GWh', year=year, available_years=list(range(year-4,year+1)),
                    source_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                    records=[r for r in records if r['year'] >= year - 4],
                    cross_table_max_gap_gwh=max(cross_checks),
                    excluded_historical_conflicts=historical_gaps, active_small_differences=active_gaps,
                    limitations=['Official aggregate data; no plant-level cleaning validation.',
                                 'Residual generation includes other fuels and storage; it is not renewable generation.',
                                 'Cross-vintage changes are revisions, not year-on-year movement.'])
    finally:
        book.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', required=True)
    p.add_argument('--year', type=int, required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    Path(a.out).write_text(json.dumps(normalize(a.data, a.year), ensure_ascii=False, indent=2)+'\n')
