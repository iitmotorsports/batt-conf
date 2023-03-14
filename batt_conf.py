from math import sqrt
import os
from typing import List
import importlib

try:
    import openpyxl
    import pandas
except ImportError:
    print("Some required packages are missing. Installing now...")
    os.system('pip install -r requirements.txt')
    importlib.invalidate_caches()

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Color
from openpyxl.utils.cell import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows

from cell import CELLS
from calc import config_t

# Range Check
RANGE_SEGMENT_SERIES = list(range(1, 25))
RANGE_SEGMENT_PARALLEL = list(range(1, 65))
RANGE_ACCUMULATOR_SEGMENTS_SERIES = list(range(1, 13))
RANGE_ACCUMULATOR_SEGMENTS_PARALLEL = list(range(1, 2))

RANGES = (
    RANGE_SEGMENT_SERIES,
    RANGE_SEGMENT_PARALLEL,
    RANGE_ACCUMULATOR_SEGMENTS_SERIES,
    RANGE_ACCUMULATOR_SEGMENTS_PARALLEL,
)

# Targets
VOLT_TARGET = 400
VOLT_MAX = 600
VOLT_MIN = 350
CAP_TOTAL_MAX_WH = 10000
CAP_TOTAL_MIN_WH = 2000
CAP_SEGMENT_MAX_MJ = 6.1
VOLT_SEGMENT_MAX = 120.1

# ADDITIONAL_CONFIG = [
#     (6, 1, 16, 8),
# ]

favorLarge = ColorScaleRule(
    start_type='min', start_color=Color(rgb='ea0c01'),
    mid_type='percentile', mid_value=50, mid_color=Color(rgb='fef301'),
    end_type='max', end_color=Color(rgb='0ba60a')
)
favorSmall = ColorScaleRule(
    start_type='min', start_color=Color(rgb='0ba60a'),
    mid_type='percentile', mid_value=50, mid_color=Color(rgb='fef301'),
    end_type='max', end_color=Color(rgb='ea0c01')
)
suggestLarge = ColorScaleRule(
    start_type='min', start_color=Color(rgb='ffffff'),
    end_type='max', end_color=Color(rgb='006796')
)
suggestSmall = ColorScaleRule(
    start_type='min', start_color=Color(rgb='006796'),
    end_type='max', end_color=Color(rgb='ffffff')
)

conditionals = {
    "V∆": suggestLarge,
    "Price": favorSmall,
    "Kg": favorSmall,
    "m³": favorSmall,
    "Power Nom kW": favorLarge,
    "Power Max kW": favorLarge,
    "Typ Cap Wh": favorLarge,
    "Max Cap Wh": favorLarge,
    "Wh/Kg": favorLarge,
    "kW/Kg": favorLarge,
    "Discharge Cont. A": favorLarge,
    "Discharge Peak A": favorLarge,
}

accending_sort = [
    ('Price', True),
    ('Kg', True),
    ('Max Cap Wh', False),
    ('Power Max kW', False),
    ('Typ Cap Wh', False),
    ('Power Nom kW', False),
    ('Power Nom kW', False),
    ('Wh/Kg', False),
    ('kW/Kg', False),
]

# for ss, sp, s, p in ADDITIONAL_CONFIG:
#     RANGE_SEGMENT_SERIES.append(ss)
#     RANGE_SEGMENT_PARALLEL.append(sp)
#     RANGE_ACCUMULATOR_SEGMENTS_SERIES.append(s)
#     RANGE_ACCUMULATOR_SEGMENTS_PARALLEL.append(p)

results: List[config_t] = []

for cell_sel in CELLS:
    for pk_parallel in RANGE_ACCUMULATOR_SEGMENTS_PARALLEL:
        for pk_series in RANGE_ACCUMULATOR_SEGMENTS_SERIES:
            for c_parallel in RANGE_SEGMENT_PARALLEL:
                for c_series in RANGE_SEGMENT_SERIES:
                    if c_series != 1 and c_series % 2 != 0:
                        continue
                    conf = config_t(cell_sel, pk_parallel, pk_series, c_parallel, c_series, VOLT_TARGET)
                    if VOLT_MIN <= conf.total_volt_nominal <= VOLT_MAX and CAP_TOTAL_MIN_WH <= conf.total_typ_capacity_wh <= CAP_TOTAL_MAX_WH:
                        if conf.segment_volt_max <= VOLT_SEGMENT_MAX and conf.segment_typ_capacity_mj <= CAP_SEGMENT_MAX_MJ:
                            results.append(conf)

df = pd.DataFrame([[y for y in x.info().values()] for x in results], columns=list(results[0].info().keys()))
for k, v in accending_sort:
    df.sort_values(k, ascending=v, inplace=True)

wb = Workbook()
ws = wb.active

for r in dataframe_to_rows(df, index=False, header=True):
    ws.append(r)

ws.auto_filter.ref = ws.dimensions

for i, cell in enumerate(ws[1], start=1):
    if cell.value in conditionals:
        letter = get_column_letter(i)
        ws.conditional_formatting.add(f"{letter}2:{letter}{len(results)*2}", conditionals[cell.value])  # IMPROVE: extend to the entire column

for column in ws.columns:
    max_length = 0
    column_dimensions = column[0].column_letter
    for cell in column:
        try:
            if len(str(cell.value)) > max_length:
                max_length = len(str(cell.value))
        except TypeError:
            pass
    adjusted_width = max_length + (10 / sqrt(max_length+1))
    ws.column_dimensions[column_dimensions].width = adjusted_width

wb.save('output.xlsx')
os.system('output.xlsx')
