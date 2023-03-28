import cadquery as cq
import argparse
import sys
import progress_bar

from pack import gen_pack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cell_name', help='Cell name from cells.csv')
    parser.add_argument('num_rows', help='Number of rows in pack', type=int)
    parser.add_argument('num_cols', help='Number of columns in pack', type=int)
    parser.add_argument('-dp', '--disable_progress', help='Disable progress bar', action='store_true')
    parser.add_argument('-f', '--force', help='Force regeneration', action='store_true')
    args = parser.parse_args()
    if args.disable_progress:
        progress_bar.CQ_EDITING = True
    print(f"\nFILE:{gen_pack(args.cell_name, args.num_rows, args.num_cols, force=args.force)}")


if __name__ == '__main__':
    main()

if 'cq_editor' in sys.modules:
    pack = gen_pack("Molicel INR18650-P28B", 4, 3, export=False)
    model = cq.Workplane("XY").add(pack.toCompound()).rotate((0, -1, 0), (0, 1, 0), 90)
    show_object(pack)
    show_object(model)
