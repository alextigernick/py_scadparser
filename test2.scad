       
function spur_gear() =
    let(  
        dummy = !is_undef(interior) ? echo("In spur_gear(), the argument 'interior=' has been deprecated, and may be removed in the future.  Please use 'internal=' instead."):0
    ) reorient(anchor,spin,orient, h=thickness, r=anchor_rad, p=vnf);