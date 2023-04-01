import math
import os
from math import sqrt
import importlib
import sys

try:
    import pandas as pd
    import cadquery as cq
except ImportError:
    print("Some required packages are missing. Installing now...")
    os.system('pip install -r requirements.txt')
    importlib.invalidate_caches()

import pandas as pd  # manually add to CQ if editing
import cadquery as cq

from cell_cylinder import gen_cell, gen_cell_lowres
from progress_bar import progress_bar

try:
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
except NameError:
    os.chdir(os.path.dirname(os.path.realpath("__file__")))

if not os.path.exists('models'):
    os.makedirs('models')

# FIXME: not staggered is broken


def gen_pack(
    cell_name, num_rows, num_cols,
    pcm_spacing_mm=2,
    collector_thickness_mm=1,
    # busbar_width_mm=25.4,
    busbar_width_mm=34.925,
    busbar_thickness_mm=6.35,
    staggered=True, highres=True, step=True, force=False, export=True,
):
    progress = progress_bar("Generating Pack Model", num_rows, num_cols)

    num_rows = int(num_rows)  # Parallel
    num_cols = int(num_cols)  # Series

    # TODO: ability to 'stack' current collection across multiple rows

    filename = os.path.join('models', f'pack_{cell_name}_{num_rows}_{num_cols}_{pcm_spacing_mm}_{staggered}'.replace(
        " ", '_').replace("-", '_').replace(".", '_'))

    if export and not force and os.path.exists(f'{filename}.stl'):
        progress.close()
        return f'{filename}.stl'

    progress.text("Reading parameters")
    df = pd.read_csv('cells.csv')
    df = df[df['cell_name'] == cell_name]
    cell_diameter = int(df['diameter'])
    cell_length = int(df['height'])

    busbar_spacing_mm = busbar_width_mm * 0.25
    busbar_length_mm = (pcm_spacing_mm + cell_diameter) * num_rows + (cell_diameter / 2) - (pcm_spacing_mm/2)

    busbar_bolt_head_height_mm = 6
    busbar_bolt_head_radius_mm = 14/2
    busbar_bolt_thread_radius_mm = 6/2 + 0.1
    busbar_bolt_thread_height_mm = 16
    busbar_nut_height_mm = 7.3
    busbar_nut_radius_mm = 14.2/2

    term_bolt_head_height_mm = 8.1
    term_bolt_head_radius_mm = 20/2
    term_bolt_thread_radius_mm = 8/2 + 0.1
    term_bolt_thread_height_mm = 20

    formex_thickness_mm = 1  # TODO

    progress.update(10, "Creating Cylinder Cell")

    # Create a cell cylinder
    if highres:
        cell, top_radius, wrap_radius = gen_cell(cell_diameter, cell_length)
    else:
        cell, top_radius, wrap_radius = gen_cell_lowres(cell_diameter, cell_length)

    progress.update(10, "Duplicating cells")

    collector_radius = max(min(wrap_radius * 1.25, (cell_diameter - pcm_spacing_mm*2)/2), top_radius*1.5)
    collector_pad_out_radius = collector_radius * 0.75
    collector_pad_in_radius = collector_radius * 0.5
    collector_fuse_dist = collector_pad_out_radius - collector_pad_in_radius
    collector_fuse_width = (collector_pad_out_radius-collector_pad_in_radius) / 1.5  # TODO: current capacity of nickel
    collector_bend_radius = collector_thickness_mm * 2
    collector_inner_bend_radius = collector_thickness_mm

    points = []
    stag = (cell_diameter / 2 + pcm_spacing_mm / 2)
    dist = sqrt(((cell_diameter + pcm_spacing_mm)**2) - (stag**2))
    for j in range(num_rows):
        y = j * (cell_diameter + pcm_spacing_mm)
        flip = True
        for i in range(num_cols):
            flip = not flip
            points.append((flip, (i * (dist), y + (0 if i % 2 == 0 else stag), 0 if flip else 0)))
            progress.update(0.5)

    cells = [(cell.translate(p).rotateAboutCenter((0, 1, 0), 180) if f else cell.translate(p)).val().Solids()[0] for f, p in points]
    progress.update(5)
    cells = [cell.moved(cq.Location((0, 0, -cq.Workplane("XY").add(cell).faces("<Z").workplane().val().Center().z))).clean() for cell in cells]
    progress.update(5)
    cells[0] = cq.Workplane("XY").add(cells[0])

    progress.update(5)

    for i, cell in enumerate(cells[1:]):
        cells[0].add(cell)
        progress.update(0.5)
    cells = cells[0]

    progress.update(10, "Cutting PCC")
    box = cq.Workplane('XY').box(
        (dist * (num_cols - 1)) + cell_diameter + pcm_spacing_mm * 2,
        ((num_rows + 0.5) * (cell_diameter + pcm_spacing_mm)) + pcm_spacing_mm,
        cell_length/2,
        centered=False
    ).translate((-pcm_spacing_mm - cell_diameter/2, -pcm_spacing_mm - cell_diameter / 2, cell_length/4))
    progress.update(5)
    box = box.cut(cells)
    progress.update(5)
    box = box.faces("<Z").wires().toPending().extrude(-cell_length/4).faces(">Z").wires().toPending().extrude(cell_length/4)
    progress.update(5, "Assembing cells and PCC")
    battery_pack = cq.Assembly()
    battery_pack = battery_pack.add(cells.clean(), color=cq.Color(94/255, 177/255, 89/255, 1))
    progress.update(5)
    battery_pack = battery_pack.add(box.clean(), color=cq.Color(30/255, 32/255, 38/255, 1))
    progress.update(5, "Current Collector")

    def plate(flipped, positive):
        flip = -1 if flipped else 1
        _box = box.faces("<Z" if flipped else ">Z").edges("%CIRCLE")
        add = 1 if flipped else 0
        it = list(range(1+add, num_cols + 1, 2))
        tag = False
        if flipped:
            it.insert(0, 1)
        progress.update(5)
        dbl_tag = False
        reverse_out = 1
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
            if tag:
                if dbl_tag:
                    reverse_out = -1
                else:
                    dbl_tag = True
            same_side = reverse_out < 0
            plate_edges = plate.objects
            plate_sk = plate.edges(">>Y[-1]" if (flipped and col != 1) else "<<Y[-1]")
            _plate = plate_sk
            plate_sk = plate_sk.sketch()

            for s in plate_edges:
                plate_sk = plate_sk.edge(s)

            if tag and num_rows == 1:
                plate = plate_sk.edges().circle(collector_radius)
            else:
                plate = plate_sk.edges().hull()
            plate = plate.finalize().extrude(flip*collector_thickness_mm, combine=False)
            if col > 1:  # FIXME: shouldn't need this part
                z_push = -cell_length if not flipped and num_rows == 1 else 0
                plate = plate.translate((-dist*(col-1), add*(-(cell_diameter + pcm_spacing_mm)*(num_rows-0.5)), z_push))

            if tag:
                cell_to_collector = ((cell_diameter/2) - collector_radius)
                pre_bend_width = collector_radius + pcm_spacing_mm + cell_to_collector  # Collector is flush on edge with pcc
                pre_bend_width += busbar_bolt_head_height_mm + formex_thickness_mm  # busbar goes on outside # add tolerance?
                pre_bend_width += collector_inner_bend_radius
                clad_height = ((num_rows-1) * ((collector_radius*2) + pcm_spacing_mm + cell_to_collector*2)) + (collector_radius*2)
                clad_height = clad_height if (num_rows > 1) else (collector_radius*2)
                post_bend_width = busbar_width_mm + busbar_spacing_mm + collector_inner_bend_radius

                plate_sk = _plate.sketch().rect(pre_bend_width, clad_height)
                plate_sk = plate_sk.finalize().extrude(flip*collector_thickness_mm, combine=False)
                plate_sk = plate_sk.translate((reverse_out*flip*(pre_bend_width/2), reverse_out*(clad_height/2 - collector_radius), 0))
                plate_sk_ext = plate_sk.faces(">X[-1]" if (col != 1 or (not flipped and num_cols == 1)) else "<X[-1]")
                plate_sk_ext = plate_sk_ext.sketch().rect(collector_thickness_mm, clad_height).finalize().extrude(-flip*post_bend_width, combine=False)
                plate_sk_ext = plate_sk_ext.translate((-flip*reverse_out*collector_thickness_mm/2, 0, -flip*collector_thickness_mm/2))
                plate: cq.Workplane = plate.union(plate_sk)
                plate = plate.union(plate_sk_ext)
                plate = plate.edges("|Y").edges("<<Z[-1]" if flipped else ">>Z[-1]").edges(">>X[-1]" if same_side or not flipped else "<<X[-1]")
                plate = plate.fillet(collector_bend_radius)
                plate = plate.edges("|Y").edges("<<Z[-2]" if flipped else ">>Z[-2]").edges(">>X[-1]" if same_side or not flipped else "<<X[-1]")
                plate = plate.fillet(collector_inner_bend_radius)

                # Bus bar

                add_bar = plate.faces(">>Y").edges("<<X" if flipped and not same_side else ">>X").first().sketch()
                shave = 0
                if same_side:
                    shave = (cell_diameter + pcm_spacing_mm)/2
                add_bar = add_bar.rect(busbar_width_mm, busbar_thickness_mm).finalize().extrude(shave-busbar_length_mm, combine=False)
                if same_side:
                    add_bar = add_bar.translate((0, 0, -shave/2))
                add_bar = add_bar.rotateAboutCenter((1, 0, 0), 90)
                add_bar = add_bar.rotateAboutCenter((0, 1, 0), 90)
                add_bar = add_bar.translate((
                    reverse_out*flip*(busbar_thickness_mm)/2,
                    (pcm_spacing_mm*1.5 + cell_diameter - collector_radius)-(busbar_length_mm/2)-(shave/2),
                    busbar_length_mm/2
                ))
                add_bar = add_bar.edges("|Y").fillet(busbar_thickness_mm/2.00001)
                hole = add_bar.edges("<<Y").edges(">>X" if same_side or not flipped else "<<X").sketch()
                hole = hole.circle(busbar_bolt_thread_radius_mm).finalize().extrude(busbar_thickness_mm*2, combine=False)
                hole = hole.rotateAboutCenter((0, 1, 0), -90)
                hole = hole.translate((-reverse_out*flip*busbar_thickness_mm, collector_radius, -busbar_thickness_mm))

                for _ in range(num_rows):
                    add_bar = add_bar.cut(hole)
                    plate = plate.cut(hole)
                    hole = hole.translate((0, collector_radius*2 + pcm_spacing_mm + cell_to_collector*2, 0))

                bolt_thread = plate.edges("%CIRCLE and >>X[-4]" if same_side or not flipped else "%CIRCLE and <<X[-4]").clean()
                bolt_thread = bolt_thread.sketch().circle(busbar_bolt_thread_radius_mm).finalize().extrude(busbar_bolt_thread_height_mm, combine=False)
                bolt_thread = bolt_thread.rotateAboutCenter((0, 1, 0), -90)
                bolt_thread = bolt_thread.translate((reverse_out*flip*busbar_bolt_thread_height_mm/2, 0, -busbar_bolt_thread_height_mm/2))
                bolts = bolt_thread
                bolt_head = bolt_thread.faces("<<X[-1]" if same_side or not flipped else ">>X[-1]")
                bolt_head = bolt_head.sketch().circle(busbar_bolt_head_radius_mm).finalize()
                bolt_head = bolt_head.extrude(busbar_bolt_head_height_mm, combine=False).rotateAboutCenter((0, 1, 0), -90)
                bolt_head = bolt_head.translate((-reverse_out*flip*busbar_bolt_head_height_mm/2, 0, -busbar_bolt_head_height_mm/2))
                bolts = bolts.union(bolt_head)
                
                nut = add_bar.edges(">>X" if same_side or not flipped else "<<X").edges("%CIRCLE")
                nut = nut.sketch().circle(busbar_nut_radius_mm).finalize()
                nut = nut.extrude(busbar_nut_height_mm, combine=False).rotateAboutCenter((0, 1, 0), -90)
                nut = nut.translate((reverse_out*flip*busbar_nut_height_mm/2, 0, -busbar_nut_height_mm/2))
                nut = nut.cut(bolts)
                bolts = bolts.add(nut)

                battery_pack.add(bolts, color=cq.Color(151/255, 162/255, 167/255, 1))
                battery_pack.add(add_bar, color=cq.Color(152/255, 87/255, 57/255, 1))

            plate_pnts = plate_pnts.sketch()
            plate_pnts = plate_pnts.circle(collector_pad_out_radius).circle(collector_pad_in_radius, mode="s").clean()
            plate_pnts = plate_pnts.rect(collector_fuse_width, collector_pad_out_radius*2, mode="s")
            plate_pnts = plate_pnts.clean().finalize().extrude(collector_thickness_mm*flip, combine=False).clean()  # Using both breaks it?

            plate = plate.cut(plate_pnts)

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
        progress.update(5)
        return positive

    positive = True if num_cols % 2 == 0 else False
    positive = plate(False, positive)
    plate(True, positive)

    progress.close()

    if export:
        battery_pack.save(f'{filename}.stl', tolerance=0.8, angularTolerance=0.8)
        if step:
            battery_pack.save(f'{filename}.step')

        return f'{filename}.stl'
    else:
        return battery_pack


def move_asm(asm: cq.Assembly, vec: cq.Vector) -> cq.Assembly:
    fnl = cq.Assembly()
    for child in asm.children:
        fnl.add(child.toCompound().translate(vec), color=child.color)
    return fnl


if 'cq_editor' in sys.modules:
    HIGH_RES = False
    show_object(gen_pack("Molicel INR21700-P45B", 2, 2, export=False, highres=HIGH_RES))
    show_object(move_asm(gen_pack("Molicel INR21700-P45B", 2, 3, export=False, highres=HIGH_RES), (0, 75, 0)))
    show_object(move_asm(gen_pack("Molicel INR21700-P45B", 1, 2, export=False, highres=HIGH_RES), (100, 0, 0)))
    show_object(move_asm(gen_pack("Molicel INR21700-P45B", 1, 3, export=False, highres=HIGH_RES), (100, 75, 0)))
    show_object(move_asm(gen_pack("Molicel INR21700-P45B", 5, 1, export=False, highres=HIGH_RES), (-100, 0, 0)))
    show_object(move_asm(gen_pack("Molicel INR21700-P45B", 3, 4, export=False, highres=HIGH_RES), (-100, -100, 0)))
    show_object(move_asm(gen_pack("Molicel INR21700-P45B", 4, 7, export=False, highres=HIGH_RES), (-100, 75*2, 0)))
    log("Done")
