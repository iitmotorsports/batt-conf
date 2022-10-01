# Cell - Molicel INR21700-P45B
VOLT_MAX = 4.2
VOLT_NOMINAL = 3.6
VOLT_MIN = 2.5

CAP_TYPICAL_AH = 4.5  # * 0.912
CAP_MIN_AH = 4.3

DISCHARGE_AMPS = 45
CHARGE_AMPS = 4.5

WEIGHT_GRAM = 66.8

# Cell - Molicel INR18650-P28B
# VOLT_MAX = 4.2
# VOLT_NOMINAL = 3.6
# VOLT_MIN = 2.5

# CAP_TYPICAL_AH = 2.8
# CAP_MIN_AH = 2.65

# DISCHARGE_AMPS = 40
# CHARGE_AMPS = 2.8

# WEIGHT_GRAM = 45.4

# Range Check
RANGE_PACK_SERIES = range(1, 32)
RANGE_PACK_PARALLEL = range(1, 32)
RANGE_ACCUMULATOR_PACKS_SERIES = range(1, 12)
RANGE_ACCUMULATOR_PACKS_PARALLEL = range(1, 12)

# Targets
VOLT_TARGET_MAX = 555
VOLT_TARGET_MIN = 545
CAP_TOTAL_MAX_WH = 5405.5
CAP_TOTAL_MIN_WH = CAP_TOTAL_MAX_WH * 0.7
CAP_SEGMENT_MAX_MJ = 6.5
VOLT_SEGMENT_MAX = 120.5

# Config

VOLT_TARGET_MAX = 355
VOLT_TARGET_MIN = 345


class config:
    total_cells = 0
    total_voltage_nominal = 0
    total_voltage_max = 0
    typ_accumulator_capacity_wh = 0
    typ_segment_capacity_mj = 0
    max_accumulator_capacity_wh = 0
    max_segment_capacity_mj = 0

    def __init__(self, pack_parallel: float, pack_series: float, parallel: float, series: float) -> None:
        self.parallel = parallel
        self.series = series
        self.pack_parallel = pack_parallel
        self.pack_series = pack_series
        self.packs = pack_parallel * pack_series
        self.pack_cells = parallel * series
        self.total_cells = self.pack_cells * self.packs
        self.weight = self.total_cells * WEIGHT_GRAM
        self.total_voltage_nominal = series * pack_series * VOLT_NOMINAL
        self.total_voltage_max = series * pack_series * VOLT_MAX
        self.typ_accumulator_capacity_wh = self.total_cells * VOLT_NOMINAL * CAP_TYPICAL_AH * 0.8
        self.typ_segment_capacity_mj = self.pack_cells * VOLT_NOMINAL * CAP_TYPICAL_AH * 0.0036
        self.max_accumulator_capacity_wh = self.total_cells * VOLT_MAX * CAP_TYPICAL_AH * 0.8
        self.max_segment_capacity_mj = self.pack_cells * VOLT_MAX * CAP_TYPICAL_AH * 0.0036
        self.segment_volt_nominal = series * VOLT_NOMINAL
        self.segment_volt_max = series * VOLT_MAX

    def __str__(self) -> str:
        params = {
            "total_cells": self.total_cells,
            "packs": self.packs,
            "pack_parallel": self.pack_parallel,
            "pack_series": self.pack_series,
            "parallel": self.parallel,
            "series": self.series,
            "weight (kg)": self.weight/1000,
            "total_voltage_nominal": self.total_voltage_nominal,
            "total_voltage_max": self.total_voltage_max,
            "segment_volt_nominal": self.segment_volt_nominal,
            "segment_volt_max": self.segment_volt_max,
            "typ_accumulator_capacity_Wh": self.typ_accumulator_capacity_wh,
            "typ_segment_capacity_MJ": self.typ_segment_capacity_mj,
            "max_accumulator_capacity_Wh": self.max_accumulator_capacity_wh,
            "max_segment_capacity_MJ": self.max_segment_capacity_mj,
        }
        mystring = "CONF\n" + ' '.join(['\t' + k + " : " + str(v) + '\n' for k, v in params.items()])
        return mystring


for pk_parallel in RANGE_ACCUMULATOR_PACKS_PARALLEL:
    for pk_series in RANGE_ACCUMULATOR_PACKS_SERIES:
        for c_parallel in RANGE_PACK_PARALLEL:
            if c_parallel % 2 != 0:
                continue
            for c_series in RANGE_PACK_SERIES:
                if c_series % 2 != 0:
                    continue
                conf = config(pk_parallel, pk_series, c_parallel, c_series)
                if VOLT_TARGET_MIN <= conf.total_voltage_max <= VOLT_TARGET_MAX and CAP_TOTAL_MIN_WH <= conf.typ_accumulator_capacity_wh <= CAP_TOTAL_MAX_WH:
                    if conf.segment_volt_max <= VOLT_SEGMENT_MAX and conf.typ_segment_capacity_mj <= CAP_SEGMENT_MAX_MJ:
                        print(conf)
