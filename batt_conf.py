import csv
from typing import List
from cell import CELLS
from calc import config_t

# Range Check
RANGE_SEGMENT_SERIES = range(1, 32)
RANGE_SEGMENT_PARALLEL = range(1, 32)
RANGE_ACCUMULATOR_SEGMENTS_SERIES = range(1, 12)
RANGE_ACCUMULATOR_SEGMENTS_PARALLEL = range(1, 2)

# Targets
VOLT_TARGET = 350
VOLT_MARGIN = 60
CAP_TOTAL_MAX_WH = 5405.5
CAP_TOTAL_MIN_WH = CAP_TOTAL_MAX_WH * 0.75
CAP_SEGMENT_MAX_MJ = 6.5
VOLT_SEGMENT_MAX = 120.5

results: List[config_t] = []

for cell_sel in CELLS:
    for pk_parallel in RANGE_ACCUMULATOR_SEGMENTS_PARALLEL:
        for pk_series in RANGE_ACCUMULATOR_SEGMENTS_SERIES:
            if pk_parallel * pk_series % 2 != 0:
                continue
            for c_parallel in RANGE_SEGMENT_PARALLEL:
                if c_parallel != 1 and c_parallel % 2 != 0:
                    continue
                for c_series in RANGE_SEGMENT_SERIES:
                    if c_series != 1 and c_series % 2 != 0:
                        continue
                    conf = config_t(cell_sel, pk_parallel, pk_series, c_parallel, c_series, VOLT_TARGET)
                    if VOLT_TARGET - VOLT_MARGIN <= conf.total_volt_nominal <= VOLT_TARGET + VOLT_MARGIN and CAP_TOTAL_MIN_WH <= conf.total_typ_capacity_wh <= CAP_TOTAL_MAX_WH:
                        if conf.segment_volt_max <= VOLT_SEGMENT_MAX and conf.segment_typ_capacity_mj <= CAP_SEGMENT_MAX_MJ:
                            results.append(conf)

with open("output.csv", 'w', encoding='utf-8') as csvfile:
    f = csv.writer(csvfile, dialect='excel', lineterminator='\n')
    f.writerow(results[0].info().keys())
    f.writerows([x.info().values() for x in results])
