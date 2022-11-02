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

    def __init__(self, name: str, volt_max: float, volt_nominal: float, volt_min: float, cap_typical_ah: float, cap_min_ah: float, discharge_cont_amps: float, discharge_peak_amps: float, charge_amps: float, weight_gram: float, height: float, diameter: float) -> None:
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


# Cells

LG_HG2 = cell_t("LG 18650HG2",
                volt_max=4.2,
                volt_nominal=3.6,
                volt_min=2.5,
                cap_typical_ah=3.0,
                cap_min_ah=3.0,
                discharge_cont_amps=7.9,
                discharge_peak_amps=20,
                charge_amps=1.25,
                weight_gram=48
                )

S_50S = cell_t("Samsung INR21700-50S",
               volt_max=4.2,
               volt_nominal=3.6,
               volt_min=2.5,
               cap_typical_ah=5.0,
               cap_min_ah=4.8,
               discharge_cont_amps=16.9,
               discharge_peak_amps=29.2,

               charge_amps=6,
               weight_gram=72)

S_40T = cell_t("Samsung INR21700-40T",
               volt_max=4.2,
               volt_nominal=3.6,
               volt_min=2.5,
               cap_typical_ah=4.0,
               cap_min_ah=3.9,
               discharge_cont_amps=21.5,
               discharge_peak_amps=45,
               charge_amps=2,
               weight_gram=70)

P45B = cell_t("Molicel INR21700-P45B",
              volt_max=4.2,
              volt_nominal=3.6,
              volt_min=2.5,
              cap_typical_ah=4.5,
              cap_min_ah=4.3,
              discharge_cont_amps=22.9,
              discharge_peak_amps=45,
              charge_amps=4.5,
              weight_gram=70)

P42A = cell_t("Molicel INR21700-P42A",
              volt_max=4.2,
              volt_nominal=3.6,
              volt_min=2.5,
              cap_typical_ah=4.2,
              cap_min_ah=4.0,
              discharge_cont_amps=21.5,
              discharge_peak_amps=45,
              charge_amps=4.2,
              weight_gram=70)

P28B = cell_t("Molicel INR18650-P28B",
              volt_max=4.2,
              volt_nominal=3.6,
              volt_min=2.5,
              cap_typical_ah=2.8,
              cap_min_ah=2.65,
              discharge_cont_amps=19,
              discharge_peak_amps=40,
              charge_amps=2.8,
              weight_gram=48)

P28A = cell_t("Molicel INR18650-P28A",
              volt_max=4.2,
              volt_nominal=3.6,
              volt_min=2.5,
              cap_typical_ah=2.8,
              cap_min_ah=2.6,
              discharge_cont_amps=17.8,  # Estimated
              discharge_peak_amps=35,
              charge_amps=2.8,
              weight_gram=48)

CELLS = (P42A, P45B, S_50S, S_40T, P28B, P28A, LG_HG2)
