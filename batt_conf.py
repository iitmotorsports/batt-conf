import csv
from typing import List
from cell import CELLS
from calc import config_t

# Range Check
RANGE_SEGMENT_SERIES = list(range(1, 25))
RANGE_SEGMENT_PARALLEL = list(range(1, 65))
RANGE_ACCUMULATOR_SEGMENTS_SERIES = list(range(1, 13))
RANGE_ACCUMULATOR_SEGMENTS_PARALLEL = list(range(1, 2))

# Targets
VOLT_TARGET = 250
VOLT_MAX = 600
VOLT_MIN = 300
CAP_TOTAL_MAX_WH = 10000
CAP_TOTAL_MIN_WH = 3000
CAP_SEGMENT_MAX_MJ = 6.1
VOLT_SEGMENT_MAX = 120.1

ADDITIONAL_CONFIG = [
    (6, 1, 16, 8),
]

for ss, sp, s, p in ADDITIONAL_CONFIG:
    RANGE_SEGMENT_SERIES.append(ss)
    RANGE_SEGMENT_PARALLEL.append(sp)
    RANGE_ACCUMULATOR_SEGMENTS_SERIES.append(s)
    RANGE_ACCUMULATOR_SEGMENTS_PARALLEL.append(p)

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

with open("output.csv", 'w', encoding='utf-8') as csvfile:
    f = csv.writer(csvfile, dialect='excel', lineterminator='\n')
    f.writerow(results[0].info().keys())
    f.writerows([x.info().values() for x in results])
