import cadquery as cq
import argparse
import sys

from pack import gen_pack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cell_name', help='Cell name from cells.csv')
    parser.add_argument('num_rows', help='Number of rows in pack', type=int)
    parser.add_argument('num_cols', help='Number of columns in pack', type=int)
    args = parser.parse_args()
    print(f"\nFILE:{gen_pack(args.cell_name, args.num_rows, args.num_cols)}")


if __name__ == '__main__':
    main()

if 'cq_editor' in sys.modules:
    pack = gen_pack("Molicel INR18650-P28B", 4, 3, export=False)
    model = cq.Workplane("XY").add(pack.toCompound()).rotate((0, -1, 0), (0, 1, 0), 90)
    show_object(pack)
    show_object(model)
