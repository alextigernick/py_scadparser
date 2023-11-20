module a()
  cube([10, 10, 10]);

module bla (  first    ,second, third,fourth) {

    local = first ? second[0] : third;
}

module blub(first) bla(blub);
module blub2(first) bla(0, [0, 0], 0, 0);

function aaa(a) = a * 2;
function bbb(c) = let(a=1) a==1?b(a,c):2;


assert(true);
function pitch_radius(
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


flit = function(x) tan(x);

flit2 = function() 2 * cos(helical);
flit3 = function() cos(helical)*2;


for (i = [10:50])
{
    let (angle = i*360/20, r= i*2, distance = r*5)
    {
        rotate(angle, [1, 0, 0])
        translate([0, distance, 0])
        sphere(r = r);
    }
}

