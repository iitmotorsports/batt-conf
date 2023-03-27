import os
from math import sqrt
import importlib
import argparse

try:
    import pandas as pd
    import cadquery as cq
except ImportError:
    print("Some required packages are missing. Installing now...")
    os.system('pip install -r requirements.txt')
    importlib.invalidate_caches()

import pandas as pd
import cadquery as cq

from cell_cylinder import gen_cell

try:
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
except NameError:
    os.chdir(os.path.dirname(os.path.realpath("__file__")))

if not os.path.exists('models'):
    os.makedirs('models')

# FIXME: not staggered is broken


def gen_model(cell_name, num_rows, num_cols, spacing_mm=2, staggered=True, highres=True, step=True, force=False, export=True):
    num_rows = int(num_rows)  # Parallel
    num_cols = int(num_cols)  # Series

    # TODO: ability to 'stack' current collection across multiple rows

    filename = os.path.join('models', f'pack_{cell_name}_{num_rows}_{num_cols}_{spacing_mm}_{staggered}'.replace(
        " ", '_').replace("-", '_').replace(".", '_'))

    if not export and not force and os.path.exists(f'{filename}.stl'):
        return f'{filename}.stl'

    df = pd.read_csv('cells.csv')
    df = df[df['cell_name'] == cell_name]
    cell_diameter = int(df['diameter'])
    cell_length = int(df['height'])

    # Create a cell cylinder
    if highres:
        cell, top_radius, wrap_radius = gen_cell(cell_diameter, cell_length)
    else:
        cell = cq.Workplane('XY').circle(cell_diameter / 2)\
            .extrude(cell_length).edges().chamfer(1.5)\
            .faces(">Z").workplane().circle(cell_diameter/3).cutBlind(-0.5)
        top_radius = cell_diameter/3 * 0.50
        wrap_radius = cell_diameter/3 * 0.75

    collector_radius = min(wrap_radius * 1.25, (cell_diameter - spacing_mm)/2)
    collector_pad_out_radius = wrap_radius
    collector_pad_in_radius = top_radius
    collector_thick = 1
    collector_fuse_width = (collector_pad_out_radius-collector_pad_in_radius)/4  # TODO: current capacity of nickel x4

    points = []
    stag = (cell_diameter / 2 + spacing_mm / 2)
    dist = sqrt(((cell_diameter + spacing_mm)**2) - (stag**2))
    for j in range(num_rows):
        y = j * (cell_diameter + spacing_mm)
        flip = True
        for i in range(num_cols):
            flip = not flip
            points.append((flip, (i * (dist), y + (0 if i % 2 == 0 else stag), 0 if flip else 0)))

    cells = [(cell.translate(p).rotateAboutCenter((0, 1, 0), 180) if f else cell.translate(p)).val().Solids()[0] for f, p in points]
    cells = [cell.moved(cq.Location((0, 0, -cq.Workplane("XY").add(cell).faces("<Z").workplane().val().Center().z))).clean() for cell in cells]
    cells[0] = cq.Workplane("XY").add(cells[0])

    for i, cell in enumerate(cells[1:]):
        cells[0].add(cell)
    cells = cells[0]

    box = cq.Workplane('XY').box(
        (dist * (num_cols - 1)) + cell_diameter + spacing_mm * 2,
        ((num_rows + 0.5) * (cell_diameter + spacing_mm)) + spacing_mm,
        cell_length/2,
        centered=False
    ).translate((-spacing_mm - cell_diameter/2, -spacing_mm - cell_diameter / 2, cell_length/4))

    box = box.cut(cells)
    box = box.faces("<Z").wires().toPending().extrude(-cell_length/4).faces(">Z").wires().toPending().extrude(cell_length/4)

    battery_pack = cq.Assembly(cells.clean(), color=cq.Color(94/255, 177/255, 89/255, 1))
    battery_pack = battery_pack.add(box.clean(), color=cq.Color(30/255, 32/255, 38/255, 1))

    def plate(flipped, positive):
        flip = -1 if flipped else 1
        _box = box.faces("<Z" if flipped else ">Z").edges("%CIRCLE")
        add = 1 if flipped else 0
        it = list(range(1+add, num_cols + 1, 2))
        tag = False
        if flipped:
            it.insert(0, 1)
        for col in it:
            if col+1 > num_cols or (flipped and col == 1):
                plate_pnts = _box.edges(f"<<X[-{col}]")
                plate = plate_pnts.circle(collector_radius).edges("<<Y[-1] or <<Y[0]")
                tag = True
                positive = not positive
            else:
                plate_pnts = _box.edges(f"<<X[-{col}] or <<X[-{col+1}]")
                plate = plate_pnts.circle(collector_radius).edges("<<Y[-1] or <<Y[-2] or <<Y[0] or <<Y[1]")
                tag = False
            plate_edges = plate.objects
            plate = plate.edges(">>Y[-1]" if (flipped and col != 1) else "<<Y[-1]")
            plate_sk = plate.sketch()
            for s in plate_edges:
                plate_sk.edge(s)
            plate = plate_sk.hull().clean().finalize().extrude(flip*collector_thick, combine=False)
            if col > 1:  # FIXME: shouldn't need this
                plate = plate.translate((-dist*(col-1), add*(-(cell_diameter + spacing_mm)*(num_rows-0.5)), 0))

            # FIXME: potential bug?
            _ = plate_pnts.extrude(flip*collector_thick*2, combine=False)
            plate_pnts = plate_pnts.circle(collector_pad_out_radius)
            plate_pnts = plate_pnts.extrude(flip, combine=False).faces('>Z').sketch().circle(collector_pad_in_radius).rect(
                collector_pad_in_radius*4, collector_fuse_width).rect(collector_fuse_width, collector_pad_in_radius*4).clean().finalize().cutBlind(-collector_thick)
            plate = plate.cut(plate_pnts).clean()

            clr = [160/255, 165/255, 195/255, 1]
            if tag:
                if positive:
                    clr[0] *= 1.50
                    clr[1] /= 2
                    clr[2] /= 2
                else:
                    clr = [x / 8 for x in clr]
                    clr[3] = 1
            battery_pack.add(plate, color=cq.Color(*clr))
        return positive

    positive = True if num_cols % 2 == 0 else False
    positive = plate(False, positive)
    plate(True, positive)
    if export:
        battery_pack.save(f'{filename}.stl', tolerance=0.8, angularTolerance=0.8)
        if step:
            battery_pack.save(f'{filename}.step')

        return f'{filename}.stl'
    else:
        return battery_pack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cell_name', help='Cell name from cells.csv')
    parser.add_argument('num_rows', help='Number of rows in pack')
    parser.add_argument('num_cols', help='Number of columns in pack')
    args = parser.parse_args()
    print(f"\nFILE:{gen_model(args.cell_name, args.num_rows, args.num_cols)}")


if __name__ == '__main__':
    main()

show_object(gen_model("Molicel INR18650-P28B", 4, 5, export=False))
