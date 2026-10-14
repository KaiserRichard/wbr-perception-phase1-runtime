#include "mapping.hpp"
#include <cassert>
#include <iomanip>
#include <iostream>
using namespace wbr::bridge;
using namespace wbr::vio;

static Gate gate() {return {"boot","device","ros_live",2,100,10};}
static EstimateSnapshot snapshot() {
  EstimateSnapshot s;
  s.source=Stamp{100,"device"}; s.sequence=1; s.state=State::TRACKING;
  s.valid=true; s.reasons=NONE; s.map_id=7; s.T_world_camera=Transform{};
  return s;
}
static ClockEvidence clock_evidence() {return {100,"device","boot","ros_live",2,10,1234567890,20,3};}
static void policy_checks() {
  auto s=snapshot(); auto e=clock_evidence(); auto g=gate();
  assert(g.advance(s,e).pose);
  assert(g.advance(s,e).reason=="duplicate");
  e.age_upper_ns=101;
  assert(g.advance(s,e).reason=="stale_source");
  s.valid=false; s.reasons=RESET; ++s.reset_counter; ++s.epoch_id;
  assert(g.advance(s,e).reason=="reset_boundary");
  s.valid=true; s.reasons=NONE; ++s.sequence; s.source->ns=200;
  e.source_ns=200; e.age_upper_ns=20;
  assert(g.advance(s,e).pose);
  s.epoch_id=0;
  assert(g.advance(s,e).reason=="regression_latched");
  s.epoch_id=1; ++s.sequence; s.source->ns=300; e.source_ns=300;
  assert(g.advance(s,e).reason=="regression_latched");
  s=snapshot(); e=clock_evidence();
  {auto f=gate(); assert(f.advance(s,std::nullopt).reason=="clock_unavailable");}
  e.session="old";
  {auto f=gate(); assert(f.advance(s,e).reason=="clock_identity_mismatch");}
  e=clock_evidence(); e.uncertainty_ns=11;
  {auto f=gate(); assert(f.advance(s,e).reason=="clock_uncertain");}
  e=clock_evidence(); s.T_world_camera->parent="odom";
  {auto f=gate(); assert(f.advance(s,e).reason=="bad_frame");}
  s=snapshot(); s.T_world_camera->matrix[0]=2;
  {auto f=gate(); assert(f.advance(s,e).reason=="bad_pose");}
  s=snapshot(); s.covariance_availability=Availability::AVAILABLE;
  {auto f=gate(); assert(f.advance(s,e).reason=="bad_covariance_metadata");}
  s=snapshot(); e=clock_evidence();
  {auto f=gate(); assert(f.advance(s,e).pose);
    ++s.sequence; s.source=Stamp{0,"other"};
    assert(f.advance(s,e).reason=="bad_source");
    s.source=Stamp{200,"device"}; e.source_ns=200;
    assert(f.advance(s,e).pose);}
}
int main() {
  policy_checks();
  int64_t ns;
  Transform t;
  if (!(std::cin>>ns)) return 0;
  for (double &v:t.matrix) if (!(std::cin>>v)) return 2;
  if (!valid_pose(t) || ns<0 || ns>2147483647999999999LL) return 2;
  auto p=pose_fields(t,ns);
  std::cout<<p.sec<<' '<<p.nanosec<<std::setprecision(17);
  for (double v:p.position) std::cout<<' '<<v;
  for (double v:p.xyzw) std::cout<<' '<<v;
  std::cout<<'\n';
}
