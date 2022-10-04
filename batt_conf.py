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
    total_voltage_nominal = 0
    total_voltage_max = 0
    typ_accumulator_capacity_wh = 0
    typ_segment_capacity_mj = 0
    max_accumulator_capacity_wh = 0
    max_segment_capacity_mj = 0

    def __init__(self, cell: cell_t, pack_parallel: float, pack_series: float, parallel: float, series: float) -> None:
        self.cell = cell
        self.parallel = parallel
        self.series = series
        self.pack_parallel = pack_parallel
        self.pack_series = pack_series
        self.packs = pack_parallel * pack_series
        self.pack_cells = parallel * series
        self.total_cells = self.pack_cells * self.packs
        self.weight = self.total_cells * cell.weight_gram
        self.total_voltage_nominal = series * pack_series * cell.volt_nominal
        self.total_voltage_max = series * pack_series * cell.volt_max
        self.typ_accumulator_capacity_wh = self.total_cells * cell.volt_nominal * cell.cap_typical_ah * 0.8
        self.typ_segment_capacity_mj = self.pack_cells * cell.volt_nominal * cell.cap_typical_ah * 0.0036
        self.max_accumulator_capacity_wh = self.total_cells * cell.volt_max * cell.cap_typical_ah
        self.max_segment_capacity_mj = self.pack_cells * cell.volt_max * cell.cap_typical_ah * 0.0036
        self.segment_volt_nominal = series * cell.volt_nominal
        self.segment_volt_max = series * cell.volt_max

    def __lt__(self, other) -> bool:
        return self.max_accumulator_capacity_wh < other.max_accumulator_capacity_wh

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
        v_dv = round(100*abs((self.total_voltage_max - VOLT_TARGET) / VOLT_TARGET), 4)
        v_sign = '+' if VOLT_TARGET < self.total_voltage_max else '-'
        v_sign = '+' if VOLT_TARGET < self.total_voltage_max else '-'
        mystring = f"{VOLT_TARGET}V {v_sign}{v_dv}% - {self.cell.name}\n"
        mystring += ' '.join(['\t' + k + " : " + str(v) + '\n' for k, v in params.items()])
        return mystring


# Cells
S_50S = cell_t("Samsung INR21700-50S", 4.2, 3.6, 2.5, 5.0, 4.8, 45, 6, 72)
P45B = cell_t("Molicel INR21700-P45B", 4.2, 3.6, 2.5, 4.5, 4.3, 45, 4.5, 70)
P42A = cell_t("Molicel INR21700-P42A", 4.2, 3.6, 2.5, 4.2, 4.0, 45, 4.2, 70)
P28B = cell_t("Molicel INR18650-P28B", 4.2, 3.6, 2.5, 2.8, 2.65, 40, 2.8, 48)

CELLS = (P42A, P45B, S_50S, P28B)

# Range Check
RANGE_PACK_SERIES = range(1, 32)
RANGE_PACK_PARALLEL = range(1, 32)
RANGE_ACCUMULATOR_PACKS_SERIES = range(1, 12)
RANGE_ACCUMULATOR_PACKS_PARALLEL = range(1, 12)

# Targets
VOLT_TARGET = 550
VOLT_MARGIN = 20
CAP_TOTAL_MAX_WH = 5405.5
CAP_TOTAL_MIN_WH = CAP_TOTAL_MAX_WH * 0.7
CAP_SEGMENT_MAX_MJ = 6.5
VOLT_SEGMENT_MAX = 120.5

results = []

for cell_sel in CELLS:
    for pk_parallel in RANGE_ACCUMULATOR_PACKS_PARALLEL:
        for pk_series in RANGE_ACCUMULATOR_PACKS_SERIES:
            if pk_parallel * pk_series % 2 != 0:
                continue
            for c_parallel in RANGE_PACK_PARALLEL:
                if c_parallel != 1 and c_parallel % 2 != 0:
                    continue
                for c_series in RANGE_PACK_SERIES:
                    if c_series != 1 and c_series % 2 != 0:
                        continue
                    conf = config_t(cell_sel, pk_parallel, pk_series, c_parallel, c_series)
                    if VOLT_TARGET - VOLT_MARGIN <= conf.total_voltage_max <= VOLT_TARGET + VOLT_MARGIN and CAP_TOTAL_MIN_WH <= conf.typ_accumulator_capacity_wh <= CAP_TOTAL_MAX_WH:
                        if conf.segment_volt_max <= VOLT_SEGMENT_MAX and conf.typ_segment_capacity_mj <= CAP_SEGMENT_MAX_MJ:
                            results.append(conf)

results.sort()
for r in results:
    print(r)
