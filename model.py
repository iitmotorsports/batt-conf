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

os.chdir(os.path.dirname(os.path.realpath(__file__)))

if not os.path.exists('models'):
    os.makedirs('models')

# FIXME: not staggered is broken


def gen_model(cell_name, num_rows, num_cols, spacing=2, staggered=True, step=False, force=False) -> str:
    num_rows = int(num_rows)
    num_cols = int(num_cols)
    filename = os.path.join('models', f'pack_{cell_name}_{num_rows}_{num_cols}_{spacing}_{staggered}'.replace(
        " ", '_').replace("-", '_').replace(".", '_'))

    if not force and os.path.exists(f'{filename}.stl'):
        return f'{filename}.stl'

    df = pd.read_csv('cells.csv')
    df = df[df['cell_name'] == cell_name]
    cell_diameter = int(df['diameter'])
    cell_length = int(df['height'])

    # Create a cell cylinder
    cell_cylinder = cq.Workplane('XY').circle(cell_diameter / 2).extrude(cell_length)
    # TODO: proper cell model
    cell_cylinder = cell_cylinder.edges().chamfer(1.5)  # FIXME: Broken?

    # Create a single row of cells
    row = cq.Workplane('XY').moveTo(0, 0)
    dist = sqrt(((cell_diameter + spacing)**2) - ((cell_diameter / 2 + spacing / 2)**2))
    if staggered:
        for i in range(num_cols):
            if i % 2 == 0:
                row = row.union(cell_cylinder.translate((i * (dist), 0, 0)))
            else:
                row = row.union(cell_cylinder.translate((i * (dist), cell_diameter / 2 + spacing / 2, 0)))
    else:
        for i in range(num_cols):
            row = row.union(cell_cylinder.translate((i * (cell_diameter + spacing), 0, 0)))

    # Create the battery pack by stacking rows of cells
    battery_pack = cq.Workplane('XY')
    for i in range(num_rows):
        battery_pack = battery_pack.union(row.translate((0, i * (cell_diameter + spacing), 0)))

    box = cq.Workplane('XY').box(
        dist * (num_cols) + cell_diameter / 4 - spacing,  # FIXME: I don't think this is right
        (num_rows + 0.5) * (cell_diameter + spacing) + spacing,
        cell_length/2,
        centered=False
    ).translate((-spacing - cell_diameter/2, -spacing - cell_diameter / 2, cell_length/4)).cut(battery_pack).faces("<Z").wires().toPending().extrude(-cell_length/4).faces(">Z").wires().toPending().extrude(cell_length/4)
    # battery_pack = box
    battery_pack = battery_pack.add(box)

    # Export the 3D model to an STL file
    cq.exporters.export(battery_pack, f'{filename}.stl')
    if step:
        cq.exporters.export(battery_pack, f'{filename}.step')
    # os.system(f'{filename}.stl')

    return f'{filename}.stl'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cell_name', help='Cell name from cells.csv')
    parser.add_argument('num_rows', help='Number of rows in pack')
    parser.add_argument('num_cols', help='Number of columns in pack')
    args = parser.parse_args()
    print(f"FILE:{gen_model(args.cell_name, args.num_rows, args.num_cols)}")


if __name__ == '__main__':
    main()
