import csv


class cell_t:
    name: str = "Nil"
    volt_max: float = 0
    volt_nominal: float = 0
    volt_min: float = 0
    cap_typical_ah: float = 0
    cap_min_ah: float = 0
    discharge_cont_amps: float = 0
    discharge_peak_amps: float = 0
    charge_amps: float = 0
    weight_gram: float = 0
    price: float = 0

    def __init__(self, name: str, volt_max: float, volt_nominal: float, volt_min: float, cap_typical_ah: float, cap_min_ah: float, discharge_cont_amps: float, discharge_peak_amps: float, charge_amps: float, weight_gram: float, height: float, diameter: float, price: float) -> None:
        self.height = height
        self.diameter = diameter
        self.name = name
        self.volt_max = volt_max
        self.volt_nominal = volt_nominal
        self.volt_min = volt_min
        self.cap_typical_ah = cap_typical_ah
        self.cap_min_ah = cap_min_ah
        self.discharge_cont_amps = discharge_cont_amps
        self.discharge_peak_amps = discharge_peak_amps
        self.charge_amps = charge_amps
        self.weight_gram = weight_gram
        self.price = price


CELLS = []

with open('cells.csv', newline='', encoding='utf-8') as csv_file:
    reader = csv.reader(csv_file, dialect='excel')
    next(reader)
    for row in reader:
        if not row[1]:
            CELLS.append(cell_t(row[0], *[float(x) for x in row[3:]]))
