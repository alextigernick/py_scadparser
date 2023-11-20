function bbb(c) = let(a=1) a==1?b(a,c):2;

function outer_radius(
    circ_pitch,
    teeth,
    helical=0,
    mod,
    diam_pitch,
    pitch
) =
    let( circ_pitch = circular_pitch(pitch, mod, circ_pitch, diam_pitch) )
    assert(is_finite(helical))
    assert(is_finite(circ_pitch))
    circ_pitch * teeth / PI / 2 / cos(helical);


function _inherit_gear_param(name, val, pval, dflt, invert=false) =
    is_undef(val)
      ? is_undef(pval)
        ? dflt
        : (invert?-1:1)*pval
      : is_undef(pval)
        ? assert(is_finite(val), str("Invalid ",name," value: ",val))
          val
        : assert(is_finite(val), str("Invalid ",name," value: ",val)) (invert?-1:1)*val;
        
function spur_gear(
    circ_pitch,
    teeth,
    thickness,
    shaft_diam = 0,
    hide = 0,
    pressure_angle,
    clearance,
    backlash = 0.0,
    helical,
    interior,
    internal,
    profile_shift="auto",
    slices,
    herringbone=false,
    shorten=0,
    diam_pitch,
    mod,
    pitch,
    gear_spin = 0,
    atype = "pitch", 
    anchor = CENTER,
    spin = 0,
    orient = UP
) =
    let(  
        dummy = !is_undef(interior) ? echo("In spur_gear(), the argument 'interior=' has been deprecated, and may be removed in the future.  Please use 'internal=' instead."):0,
        internal = first_defined([internal,interior,false]),
        circ_pitch = _inherit_gear_pitch("spur_gear()", pitch, circ_pitch, diam_pitch, mod),
        PA = _inherit_gear_pa(pressure_angle),
        helical = _inherit_gear_helical(helical, invert=!internal),
        thickness = _inherit_gear_thickness(thickness)
    )
    assert(is_integer(teeth) && teeth>3)
    assert(is_finite(thickness) && thickness>0)
    assert(is_finite(shaft_diam) && shaft_diam>=0)
    assert(is_integer(hide) && hide>=0 && hide<teeth)
    assert(is_finite(PA) && PA>=0 && PA<90, "Bad pressure_angle value.")
    assert(clearance==undef || (is_finite(clearance) && clearance>=0))
    assert(is_finite(backlash) && backlash>=0)
    assert(is_finite(helical) && abs(helical)<90)
    assert(is_bool(herringbone))
    assert(slices==undef || (is_integer(slices) && slices>0))
    assert(is_finite(gear_spin))
    let(
        profile_shift = auto_profile_shift(teeth,PA,helical,profile_shift=profile_shift),
        pr = pitch_radius(circ_pitch, teeth, helical),
        or = outer_radius(circ_pitch, teeth, helical=helical, profile_shift=profile_shift, internal=internal,shorten=shorten),
        rr = _root_radius(circ_pitch, teeth, clearance, profile_shift=profile_shift, internal=internal),
        anchor_rad = atype=="pitch" ? pr
                   : atype=="tip" ? or
                   : atype=="root" ? rr
                   : assert(false,"atype must be one of \"root\", \"tip\" or \"pitch\""),
        circum = 2 * PI * pr,
        twist = 360*thickness*tan(helical)/circum,
        slices = default(slices, ceil(twist/360*segs(pr)+1)),
        rgn = spur_gear2d(
                circ_pitch = circ_pitch,
                teeth = teeth,
                pressure_angle = PA,
                hide = hide,
                helical = helical,
                clearance = clearance,
                backlash = backlash,
                internal = internal,
                shorten = shorten,
                profile_shift = profile_shift,
                shaft_diam = shaft_diam
            ),
        rvnf = herringbone
          ? zrot(twist/2, p=linear_sweep(rgn, height=thickness, twist=twist, slices=slices, center=true))
          : let(
                wall_vnf = linear_sweep(rgn, height=thickness/2, twist=twist/2, slices=ceil(slices/2), center=false, caps=false),
                cap_vnf = vnf_from_region(rgn, transform=up(thickness/2)*zrot(twist/2))
            )
            vnf_join([
                wall_vnf, zflip(p=wall_vnf),
                cap_vnf,  zflip(p=cap_vnf),
            ]),
        vnf = zrot(gear_spin, p=rvnf)
    ) reorient(anchor,spin,orient, h=thickness, r=anchor_rad, p=vnf);