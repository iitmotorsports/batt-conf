from __future__ import annotations
from cell import cell_t

CELL_DIAMETER_BUF_MM = 6


class config_t:
    def __init__(self, cell: cell_t, parallel_segments: float, series_segments: float, parallel: float, series: float, voltage_target: float) -> None:
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
        self.total_discharge_cont_amps = cell.discharge_cont_amps * self.parallel
        self.total_discharge_peak_amps = cell.discharge_peak_amps * self.parallel
        self.segment_typ_capacity_mj = self.segment_cells * cell.volt_nominal * cell.cap_typical_ah * 0.0036
        self.total_max_capacity_wh = self.total_cells * cell.volt_max * cell.cap_typical_ah
        self.segment_max_capacity_mj = self.segment_cells * cell.volt_max * cell.cap_typical_ah * 0.0036
        self.segment_volt_nominal = series * cell.volt_nominal
        self.segment_volt_max = series * cell.volt_max
        self.voltage_target = voltage_target
        self.segment_width = (0.866 * (self.parallel - 1) + 1) * (cell.diameter + CELL_DIAMETER_BUF_MM)
        self.segment_length = (self.segment_cells + 0.5) * (cell.diameter + CELL_DIAMETER_BUF_MM)
        self.segment_mm2 = self.segment_length * self.segment_width

    def info(self) -> dict:
        v_sign = '+' if self.voltage_target < self.total_volt_max else '-'
        v_sign = '+' if self.voltage_target < self.total_volt_max else '-'
        v_dv = round(100*abs((self.total_volt_max - self.voltage_target) / self.voltage_target), 4)
        return {
            "cell": self.cell.name,
            "target_volt_dv": f"{v_sign}{v_dv}",
            "total_cells": self.total_cells,
            "segments": self.segments,
            "parallel_segments": self.parallel_segments,
            "series_segments": self.series_segments,
            "parallel": self.parallel,
            "series": self.series,
            "weight_kg": self.weight / 1000,
            "total_volt_nominal": self.total_volt_nominal,
            "total_volt_max": self.total_volt_max,
            "total_power_nominal_kW": self.total_discharge_cont_amps * self.total_volt_nominal / 1000,  # TODO: How is power calculated?
            "total_power_max_kW": self.total_discharge_peak_amps * self.total_volt_max / 1000,
            "total_typ_capacity_wh": self.total_typ_capacity_wh,
            "total_max_capacity_wh": self.total_max_capacity_wh,
            "total_discharge_cont_amps": self.total_discharge_cont_amps,
            "total_discharge_peak_amps": self.total_discharge_peak_amps,
            "segment_volt_nominal": self.segment_volt_nominal,
            "segment_volt_max": self.segment_volt_max,
            "segment_typ_capacity_mj": self.segment_typ_capacity_mj,
            "segment_max_capacity_mj": self.segment_max_capacity_mj,
        }

    def __lt__(self, other: config_t) -> bool:
        return self.total_max_capacity_wh < other.total_max_capacity_wh

    def __str__(self) -> str:
        params = self.info()
        v_dv = params["target_volt_dv"]
        del params["cell"]
        del params["target_volt_dv"]
        mystring = f"{self.voltage_target}V {v_dv}% - {self.cell.name}\n"
        mystring += ' '.join(['\t' + k + " : " + str(v) + '\n' for k, v in params.items()])
        return mystring
