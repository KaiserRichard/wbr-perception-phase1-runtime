// OFFLINE/SYNTHETIC ONLY. These fixtures cannot qualify SDK timing or hardware.
#include "d435i_input.h"
#include <cassert>
#include <iostream>
#include <limits>

template<class F> void rejects(F fn) {
    bool rejected=false;
    try { fn(); } catch (const std::runtime_error&) { rejected=true; }
    assert(rejected);
}
int main() {
    const wbr::Sample a{1.0,{0,2,-2}}, b{1.01,{10,4,2}};
    const auto m=wbr::interpolate(a,b,1.005);
    assert(std::abs(m.x-5)<1e-10 && std::abs(m.y-3)<1e-10 && std::abs(m.z)<1e-10);
    rejects([&]{ wbr::interpolate(a,b,1.02); });
    rejects([&]{ wbr::interpolate(a,a,1.0); });
    wbr::Input input;
    input.gyro({0.999,{1,2,3}});
    input.accel(a); input.accel(b);
    input.gyro({1.003,{1,2,3}}); input.gyro({1.007,{4,5,6}});
    input.trim_prefix(); assert(input.prefix_gyro==1);
    assert(input.before_coverage(1.001));
    assert(!input.ready(1.008)); // Requires first gyro >= camera time, not stale propagation.
    const auto first=input.take(1.005);
    assert(first.size()==2 && first[0].t==1.003 && first[1].t==1.007);
    assert(std::abs(first[0].accel.x-3)<1e-10);
    assert(std::abs(first[1].accel.x-7)<1e-10);
    input.gyro({1.012,{7,8,9}});
    assert(!input.ready(1.011)); // Future accel bracket must arrive.
    input.accel({1.02,{20,6,6}});
    const auto second=input.take(1.011);
    assert(second.size()==1 && second[0].t==1.012); // Endpoint sent once, no duplicate.
    assert(std::abs(second[0].accel.x-12)<1e-10);
    rejects([&]{ input.take(1.1); });
    rejects([&]{ input.gyro({1.012,{0,0,0}}); });
    rejects([&]{ input.accel({1.015,{0,0,0}}); });
    rejects([&]{ input.gyro({1.1,{0,0,0}}); }); // Interior gap.
    rejects([&]{ input.gyro({1.015,{std::numeric_limits<double>::quiet_NaN(),0,0}}); });
    rejects([&]{ input.gyro({std::numeric_limits<double>::infinity(),{0,0,0}}); });
    std::cout << "OFFLINE/SYNTHETIC: interpolation, ordering, gaps and boundary fixtures completed; hardware OPEN\n";
}
