import cadquery as cq

DIAMETER_CONST = 18
RAD_CONST = DIAMETER_CONST / 2
LENGTH_CONST = 65.38


def gen_cell_lowres(cell_diameter: float, cell_length: float) -> tuple[cq.Workplane, float, float]:
    cell = cq.Workplane('XY').circle(cell_diameter / 2)\
        .extrude(cell_length).edges().chamfer(1.5)\
        .faces(">Z").workplane().circle(cell_diameter/3).cutBlind(-0.5)
    top_radius = (4.75 / RAD_CONST) * cell_diameter/2
    wrap_radius = (7.325 / RAD_CONST) * cell_diameter/2
    return cell, top_radius, wrap_radius


def gen_cell(cell_diameter: float, cell_length: float) -> tuple[cq.Workplane, float, float]:
    cell_radius = cell_diameter / 2

    cell_body_length = (65 / LENGTH_CONST) * cell_length

    wrap_depth = (0.2 / LENGTH_CONST) * cell_length
    wrap_radius = (7.325 / RAD_CONST) * cell_radius
    wrap_fillet = cell_radius / 10

    inner_radius = (11 / DIAMETER_CONST) * cell_diameter / 2
    inner_depth = (1 / LENGTH_CONST) * cell_length

    top_radius = (4.75 / RAD_CONST) * cell_radius
    top_leg_radius = (5.25 / RAD_CONST) * cell_radius
    top_thick = (0.5 / LENGTH_CONST) * cell_length
    top_dist = (1.5 / LENGTH_CONST) * cell_length
    top_fillet = top_thick / 3

    bottom_radius = (6 / RAD_CONST) * cell_radius
    bottom_fillet = (wrap_depth / 2) - (wrap_depth / 16)

    groove_start = (3 / LENGTH_CONST) * cell_length
    groove_end = (5.5 / LENGTH_CONST) * cell_length
    groove_len = groove_end - groove_start
    groove_offset = cell_body_length-groove_len-groove_start
    groove_radius = (8.75 / RAD_CONST) * cell_radius
    groove_radius = (cell_radius-groove_radius)*4
    groove_fillet = groove_len / 3

    cell_cylinder = cq.Workplane('XY').circle(cell_radius).extrude(cell_body_length)
    cell_cylinder = cell_cylinder.edges().chamfer(wrap_fillet)

    wrap_cut = cq.Workplane('XY').circle(wrap_radius).extrude(wrap_depth)
    cell_cylinder = cell_cylinder.cut(wrap_cut)
    wrap_cut = wrap_cut.translate((0, 0, cell_body_length-wrap_depth))
    cell_cylinder = cell_cylinder.cut(wrap_cut)

    inner_cut = cq.Workplane('XY').circle(inner_radius).extrude(inner_depth)
    inner_cut = inner_cut.translate((0, 0, cell_body_length-inner_depth-wrap_depth))
    cell_cylinder = cell_cylinder.cut(inner_cut)
    cell_cylinder = cell_cylinder.faces("<Z[-2]").workplane().circle(bottom_radius).extrude(wrap_depth).clean()
    try:
        cell_cylinder = cell_cylinder.edges("%CIRCLE and <<Z[-3]").chamfer(bottom_fillet)
        cell_cylinder = cell_cylinder.edges("%CIRCLE and <<Z[-1]").chamfer(bottom_fillet)
    except:
        pass

    num_legs = 3

    cross = cell_cylinder.faces(">Z[-3]").workplane().sketch().circle(top_leg_radius, tag="top_leg").circle(top_radius, mode="s")
    cross = cross.edges(tag="top_leg").distribute(num_legs).polygon([(0, -top_leg_radius/2), (top_leg_radius, 0), (0, top_leg_radius/2)], mode='s')
    cross = cross.clean().finalize().extrude(top_dist, combine=False).faces(">Z").workplane().circle(top_radius).extrude(-top_thick)
    try:
        cross = cross.edges("not <<Z").chamfer(top_fillet)
    except:
        pass
    cell_cylinder = cell_cylinder.union(cross)

    groove_dig_radius = cell_radius + (groove_radius / 2)
    groove = cq.Workplane('ZX').circle(groove_radius)
    groove = groove.sweep(cq.Workplane('XY').circle(groove_dig_radius).translate((groove_dig_radius, 0, 0)).edges(), sweepAlongWires=True)
    groove = groove.translate((-groove_dig_radius, 0, groove_offset))
    cell_cylinder = cell_cylinder.cut(groove)
    cell_cylinder = cell_cylinder.edges("%CIRCLE").edges(">>Z[-9] or >>Z[-11]").fillet(groove_fillet)

    return cell_cylinder.clean(), top_radius, wrap_radius


# show_object(gen_cell(18.2, 60.2)[0])
