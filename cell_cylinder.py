import cadquery as cq

DIAMETER_CONST = 18
RAD_CONST = DIAMETER_CONST / 2
LENGTH_CONST = 65.38


def gen_cell(cell_diameter: int, cell_length: int) -> tuple[cq.Workplane, float, float]:
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
    top_fillet = top_leg_radius - top_radius - top_thick / 8

    bottom_radius = (6 / RAD_CONST) * cell_radius
    bottom_fillet = (wrap_depth / 2) - (wrap_depth / 16)

    groove_start = (3 / LENGTH_CONST) * cell_length
    groove_end = (5.5 / LENGTH_CONST) * cell_length
    groove_len = groove_end - groove_start
    groove_radius = (8.75 / RAD_CONST) * cell_radius
    groove_fillet = groove_len / 3

    cell_cylinder = cq.Workplane('XY').circle(cell_radius).extrude(cell_body_length)
    cell_cylinder = cell_cylinder.edges().fillet(wrap_fillet)

    wrap_cut = cq.Workplane('XY').circle(wrap_radius).extrude(wrap_depth)
    cell_cylinder = cell_cylinder.cut(wrap_cut)
    wrap_cut = wrap_cut.translate((0, 0, cell_body_length-wrap_depth))
    cell_cylinder = cell_cylinder.cut(wrap_cut)

    inner_cut = cq.Workplane('XY').circle(inner_radius).extrude(inner_depth)
    inner_cut = inner_cut.translate((0, 0, cell_body_length-inner_depth-wrap_depth))
    cell_cylinder = cell_cylinder.cut(inner_cut)
    cell_cylinder = cell_cylinder.faces("<Z[-2]").workplane().circle(bottom_radius).extrude(wrap_depth).clean()
    try:
        cell_cylinder = cell_cylinder.edges("%CIRCLE and <<Z[-3]").fillet(bottom_fillet)
        cell_cylinder = cell_cylinder.edges("%CIRCLE and <<Z[-1]").fillet(bottom_fillet)
    except:
        pass

    # Define the circle and leg dimensions
    num_legs = 3
    leg_length = top_leg_radius * 1.2
    leg_width = top_leg_radius

    # Create a Workplane on the XY plane
    circle = cq.Workplane("XY").circle(top_leg_radius).extrude(top_dist)

    # Create the legs
    for i in range(num_legs):
        angle = i * 360 / num_legs
        leg = cq.Workplane("XY").move(0, leg_length/2)
        leg = leg.rect(leg_width, leg_length)
        leg = leg.extrude(leg_length)
        leg = leg.rotate((0, 0, -leg_length/2), (0, 0, 1), angle)
        circle = circle.cut(leg)

    circle_edges = circle.faces("<Z").edges("%CIRCLE").objects

    for edge in circle_edges:
        v1 = edge.startPoint()
        v2 = edge.endPoint()
        angle = 360 / num_legs / 2

        line1 = cq.Workplane("XY")\
            .line(v1.x, v1.y, 0)\
            .center(0, 0)\
            .line(v2.x, v2.y, 0)\
            .center(v1.x, v1.y)\
            .ellipseArc(top_leg_radius, top_leg_radius, 0, angle)\
            .center(0, 0).close()
        slic = line1.extrude(top_dist)

    cross = slic.union(slic.rotate((0, 0, 1), (0, 0, 0), 360 / num_legs))\
        .union(slic.rotate((0, 0, 1), (0, 0, 0), -360 / num_legs))

    circle = cq.Workplane("XY").circle(top_radius).extrude(top_dist*2)
    cross = cross.cut(circle)
    circle = cq.Workplane("XY").circle(top_radius).extrude(top_thick)\
        .translate((0, 0, top_dist-top_thick))
    cross = cross.union(circle).clean()
    try:
        cross = cross.toPending().faces(">Z").edges("%ELLIPSE").fillet(top_fillet)
    except:
        pass
    cross = cross.clean().translate((0, 0, cell_body_length-inner_depth-wrap_depth))

    cell_cylinder = cell_cylinder.union(cross).clean()

    groove = cq.Workplane('XY').circle(cell_radius*2).extrude(groove_len)
    groove = groove.cut(cq.Workplane('XY').circle(groove_radius).extrude(groove_len))
    groove = groove.faces("|Z").fillet(groove_fillet)
    groove = groove.translate((0, 0, cell_body_length-groove_len-groove_start))
    cc = cq.Workplane('XY').circle(cell_radius).extrude(cell_body_length).cut(groove)
    cc = cc.edges("%CIRCLE")
    cc = cc.edges(">>Z[-2] or >>Z[-7]").fillet(groove_fillet)
    cc = cq.Workplane('XY').circle(cell_radius).extrude(cell_body_length).cut(cc)
    cell_cylinder = cell_cylinder.cut(cc)

    groove = None
    cc = None
    wrap_cut = None
    inner_cut = None
    leg = None
    slic = None
    circle = None
    cross = None

    return cell_cylinder.clean(), top_radius, wrap_radius
