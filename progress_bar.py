import sys
if 'cq_editor' in sys.modules:
    CQ_EDITING = True
else:
    CQ_EDITING = False

if not CQ_EDITING:
    from tqdm import tqdm

MODEL_GEN_STEPS = 100


class progress_bar:

    def __init__(self, desc, num_rows, num_cols) -> None:
        if not CQ_EDITING:
            self.desc = desc
            self.bar = tqdm(total=MODEL_GEN_STEPS+num_rows*num_cols, desc=desc, bar_format='{l_bar}{bar}|', leave=False)

    def text(self, msg: str):
        if not CQ_EDITING:
            self.bar.set_description(f"{self.desc} : {msg}")

    def update(self, steps: float, msg=None):
        if not CQ_EDITING:
            if msg:
                self.text(msg)
            self.bar.update(steps)
            self.bar.refresh()

    def close(self):
        if not CQ_EDITING:
            self.bar.close()
