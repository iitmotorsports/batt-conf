from __future__ import annotations
from cell import cell_t
from math import pi

CELL_DIAMETER_BUF_MM = 2  # Approx 4mm of pcc between cells
PCC_DENSITY_KG_M_3 = 890


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
        self.weight_kg = self.total_cells * cell.weight_gram / 1000
        self.total_volt_nominal = series * series_segments * cell.volt_nominal
        self.total_volt_max = series * series_segments * cell.volt_max
        self.total_typ_capacity_wh = self.total_cells * cell.volt_nominal * cell.cap_typical_ah * 0.8
        self.total_discharge_cont_amps = cell.discharge_cont_amps * self.parallel
        self.total_discharge_peak_amps = cell.discharge_peak_amps * self.parallel
        self.power_nom_kw = self.total_discharge_cont_amps * self.total_volt_nominal / 1000  # TODO: How is power calculated?
        self.power_max_kw = self.total_discharge_peak_amps * self.total_volt_max / 1000
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
        self.segment_m_2 = self.segment_length * self.segment_width / 1000000
        self.volume_m_3 = self.segment_length * self.segment_width * cell.height * self.segments / 1000000000
        self.pcc_weight_kg = 0
        if PCC_DENSITY_KG_M_3:
            cell_volume_m_3 = self.total_cells * pi * ((cell.diameter / 2 / 1000) ** 2) * (cell.height / 1000)
            self.pcc_weight_kg = (self.volume_m_3 - cell_volume_m_3) * PCC_DENSITY_KG_M_3
            self.weight_kg += self.pcc_weight_kg
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
            "Total Segments": self.segments,
            "Parallel Seg": self.parallel_segments,
            "Series Seg": self.series_segments,
            "Parallel Seg Cell": self.parallel,
            "Series Seg Cell": self.series,
            "Kg": round(self.weight_kg, 2),
            "PCC Kg": round(self.pcc_weight_kg, 2),
            "m³": round(self.volume_m_3, 4),
            "Volt Nom": self.total_volt_nominal,
            "Volt Max": self.total_volt_max,
            "Power Nom kW": self.power_nom_kw,
            "Power Max kW": self.power_max_kw,
            "Typ Cap Wh": self.total_typ_capacity_wh,
            "Max Cap Wh": self.total_max_capacity_wh,
            "Wh/Kg": round(self.total_typ_capacity_wh / self.weight_kg, 4),
            "kW/Kg": round(self.power_nom_kw / self.weight_kg, 2),
            "Discharge Cont. A": self.total_discharge_cont_amps,
            "Discharge Peak A": self.total_discharge_peak_amps,
            "Seg Dim": self.segment_dim,
            "Seg m²": round(self.segment_m_2, 2),
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
