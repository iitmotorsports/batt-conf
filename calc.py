from __future__ import annotations
from cell import cell_t

CELL_DIAMETER_BUF_MM = 2


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
        # TODO: dim calc is a bit off?
        self.segment_width = (self.parallel + 0.5) * (cell.diameter + CELL_DIAMETER_BUF_MM)
        self.segment_length = (0.866 * ((self.segment_cells / self.parallel)-1) + 1) * (cell.diameter + CELL_DIAMETER_BUF_MM)
        self.segment_dim = f"{int(self.segment_length)}mm x {int(self.segment_width)}mm"
        self.segment_m_2 = round(self.segment_length * self.segment_width / 1000000, 3)
        self.volume_m_3 = round(self.segment_length * self.segment_width * cell.height * self.segments / 1000000000, 4)
        self.price = round(cell.price * self.total_cells, 2)

    def info(self) -> dict:
        v_sign = '+' if self.voltage_target < self.total_volt_nominal else '-'
        v_sign = '+' if self.voltage_target < self.total_volt_nominal else '-'
        v_dv = round(100*abs((self.total_volt_nominal - self.voltage_target) / self.voltage_target), 4)
        return {
            "Cell Name": self.cell.name,
            "V∆": f"{v_sign}{v_dv}",
            "Cells": self.total_cells,
            "Price": self.price,
            "Segments": self.segments,
            # "Parallel Seg": self.parallel_segments,
            # "Series Seg": self.series_segments,
            "Parallel Seg Cell": self.parallel,
            "Series Seg Cell": self.series,
            "Kg": round(self.weight / 1000, 2),
            "m³": self.volume_m_3,
            "Volt Nom": self.total_volt_nominal,
            "Volt Max": self.total_volt_max,
            "Power Nom kW": self.total_discharge_cont_amps * self.total_volt_nominal / 1000,  # TODO: How is power calculated?
            "Power Max kW": self.total_discharge_peak_amps * self.total_volt_max / 1000,
            "Typ Cap Wh": self.total_typ_capacity_wh,
            "Max Cap Wh": self.total_max_capacity_wh,
            "Discharge Cont. A": self.total_discharge_cont_amps,
            "Discharge Peak A": self.total_discharge_peak_amps,
            "Seg Dim": self.segment_dim,
            "Seg m²": self.segment_m_2,
            "Seg Volt Nom": self.segment_volt_nominal,
            "Seg Volt Max": self.segment_volt_max,
            "Seg Typ Cap MJ": self.segment_typ_capacity_mj,
            "Seg Max Cap MJ": self.segment_max_capacity_mj,
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
