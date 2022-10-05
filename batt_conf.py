import csv
from typing import List


class cell_t:
    name: str = None
    volt_max: float = 0
    volt_nominal: float = 0
    volt_min: float = 0
    cap_typical_ah: float = 0
    cap_min_ah: float = 0
    discharge_amps: float = 0
    charge_amps: float = 0
    weight_gram: float = 0

    def __init__(self, name: str, volt_max: float, volt_nominal: float, volt_min: float, cap_typical_ah: float, cap_min_ah: float, discharge_amps: float, charge_amps: float, weight_gram: float) -> None:
        self.name = name
        self.volt_max = volt_max
        self.volt_nominal = volt_nominal
        self.volt_min = volt_min
        self.cap_typical_ah = cap_typical_ah
        self.cap_min_ah = cap_min_ah
        self.discharge_amps = discharge_amps
        self.charge_amps = charge_amps
        self.weight_gram = weight_gram


class config_t:
    total_cells = 0
    total_volt_nominal = 0
    total_volt_max = 0
    total_typ_capacity_wh = 0
    segment_typ_capacity_mj = 0
    total_max_capacity_wh = 0
    segment_max_capacity_mj = 0

    def __init__(self, cell: cell_t, parallel_segments: float, series_segments: float, parallel: float, series: float) -> None:
        self.cell = cell
        self.parallel = parallel
        self.series = series
        self.parallel_segments = parallel_segments
        self.series_segments = series_segments
        self.segments = parallel_segments * series_segments
        self.segment_cells = parallel * series
        self.total_cells = self.segment_cells * self.segments
        self.weight = self.total_cells * cell.weight_gram
        self.total_volt_nominal = series * series_segments * cell.volt_nominal
        self.total_volt_max = series * series_segments * cell.volt_max
        self.total_typ_capacity_wh = self.total_cells * cell.volt_nominal * cell.cap_typical_ah * 0.8
        self.segment_typ_capacity_mj = self.segment_cells * cell.volt_nominal * cell.cap_typical_ah * 0.0036
        self.total_max_capacity_wh = self.total_cells * cell.volt_max * cell.cap_typical_ah
        self.segment_max_capacity_mj = self.segment_cells * cell.volt_max * cell.cap_typical_ah * 0.0036
        self.segment_volt_nominal = series * cell.volt_nominal
        self.segment_volt_max = series * cell.volt_max

    def info(self) -> dict:
        v_sign = '+' if VOLT_TARGET < self.total_volt_max else '-'
        v_sign = '+' if VOLT_TARGET < self.total_volt_max else '-'
        v_dv = round(100*abs((self.total_volt_max - VOLT_TARGET) / VOLT_TARGET), 4)
        return {
            "cell": self.cell.name,
            "target_volt_dv": f"{v_sign}{v_dv}",
            "total_cells": self.total_cells,
            "segments": self.segments,
            "parallel_segments": self.parallel_segments,
            "series_segments": self.series_segments,
            "parallel": self.parallel,
            "series": self.series,
            "weight_kg": self.weight/1000,
            "total_volt_nominal": self.total_volt_nominal,
            "total_volt_max": self.total_volt_max,
            "total_typ_capacity_wh": self.total_typ_capacity_wh,
            "total_max_capacity_wh": self.total_max_capacity_wh,
            "segment_volt_nominal": self.segment_volt_nominal,
            "segment_volt_max": self.segment_volt_max,
            "segment_typ_capacity_mj": self.segment_typ_capacity_mj,
            "segment_max_capacity_mj": self.segment_max_capacity_mj,
        }

    def __lt__(self, other) -> bool:
        return self.total_max_capacity_wh < other.total_max_capacity_wh

    def __str__(self) -> str:
        params = self.info()
        v_dv = params["target_volt_dv"]
        del params["cell"]
        del params["target_volt_dv"]
        mystring = f"{VOLT_TARGET}V {v_dv}% - {self.cell.name}\n"
        mystring += ' '.join(['\t' + k + " : " + str(v) + '\n' for k, v in params.items()])
        return mystring


# Cells
S_50S = cell_t("Samsung INR21700-50S", 4.2, 3.6, 2.5, 5.0, 4.8, 45, 6, 72)
P45B = cell_t("Molicel INR21700-P45B", 4.2, 3.6, 2.5, 4.5, 4.3, 45, 4.5, 70)
P42A = cell_t("Molicel INR21700-P42A", 4.2, 3.6, 2.5, 4.2, 4.0, 45, 4.2, 70)
P28B = cell_t("Molicel INR18650-P28B", 4.2, 3.6, 2.5, 2.8, 2.65, 40, 2.8, 48)

CELLS = (P42A, P45B, S_50S, P28B)

# Range Check
RANGE_SEGMENT_SERIES = range(1, 64)
RANGE_SEGMENT_PARALLEL = range(1, 32)
RANGE_ACCUMULATOR_SEGMENTS_SERIES = range(1, 64)
RANGE_ACCUMULATOR_SEGMENTS_PARALLEL = range(1, 3)

# Targets
VOLT_TARGET = 550
VOLT_MARGIN = 20
CAP_TOTAL_MAX_WH = 5405.5
CAP_TOTAL_MIN_WH = CAP_TOTAL_MAX_WH * 0.6
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
                    conf = config_t(cell_sel, pk_parallel, pk_series, c_parallel, c_series)
                    if VOLT_TARGET - VOLT_MARGIN <= conf.total_volt_max <= VOLT_TARGET + VOLT_MARGIN and CAP_TOTAL_MIN_WH <= conf.total_typ_capacity_wh <= CAP_TOTAL_MAX_WH:
                        if conf.segment_volt_max <= VOLT_SEGMENT_MAX and conf.segment_typ_capacity_mj <= CAP_SEGMENT_MAX_MJ:
                            results.append(conf)

with open("output.csv", 'w', encoding='utf-8') as csvfile:
    f = csv.writer(csvfile, dialect='excel')
    f.writerow(results[0].info().keys())
    f.writerows([x.info().values() for x in results])
