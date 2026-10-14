// Status: OPEN. Pure input association for synthetic checks and the proposed driver.
#pragma once
#include <cmath>
#include <deque>
#include <stdexcept>
#include <vector>

namespace wbr {
struct Vec3 { double x, y, z; };
struct Sample { double t; Vec3 v; };
struct Combined { double t; Vec3 accel, gyro; };
inline Vec3 interpolate(const Sample& a, const Sample& b, double t) {
    if (!(a.t < b.t && a.t <= t && t <= b.t))
        throw std::runtime_error("accel requires strictly ordered brackets; no extrapolation");
    const double u = (t-a.t)/(b.t-a.t);
    return {a.v.x+u*(b.v.x-a.v.x), a.v.y+u*(b.v.y-a.v.y),
            a.v.z+u*(b.v.z-a.v.z)};
}
class Input {
    std::deque<Sample> accel_, gyro_;
    double last_accel_ = -INFINITY, last_gyro_ = -INFINITY;
    static void append(std::deque<Sample>& q, double& last, Sample s) {
        if (!std::isfinite(s.t) || !std::isfinite(s.v.x) || !std::isfinite(s.v.y) ||
            !std::isfinite(s.v.z) || s.t <= last)
            throw std::runtime_error("nonfinite or duplicate/backward IMU sample");
        // Development guard only; does not replace the N2 timing thresholds.
        if (std::isfinite(last) && s.t-last > 0.05)
            throw std::runtime_error("IMU gap exceeds development guard of 50 ms");
        if (q.size() >= 4096) throw std::runtime_error("IMU queue overflow");
        last = s.t;
        q.push_back(s);
    }
public:
    unsigned long prefix_gyro = 0;
    void accel(Sample s) { append(accel_, last_accel_, s); }
    void gyro(Sample s) { append(gyro_, last_gyro_, s); }
    void trim_prefix() {
        while (!accel_.empty() && !gyro_.empty() && gyro_.front().t < accel_.front().t) {
            gyro_.pop_front(); ++prefix_gyro;
        }
    }
    bool before_coverage(double t) const {
        return !gyro_.empty() && t < gyro_.front().t;
    }
    bool ready(double t) const {
        if (accel_.size() < 2 || gyro_.empty()) return false;
        for (const auto& g : gyro_) if (g.t >= t)
            return accel_.front().t <= gyro_.front().t && accel_.back().t >= g.t;
        return false;
    }
    std::vector<Combined> take(double t) {
        if (!ready(t)) throw std::runtime_error("missing trailing gyro/accel coverage");
        std::vector<Combined> result;
        do {
            const auto g = gyro_.front(); gyro_.pop_front();
            while (accel_.size() > 2 && accel_[1].t <= g.t) accel_.pop_front();
            result.push_back({g.t, interpolate(accel_[0], accel_[1], g.t), g.v});
        } while (result.back().t < t);
        // Include the first gyro >= image stamp once. ORB retains that endpoint
        // internally for the next preintegration interval (Tracking.cc).
        return result;
    }
};
} // namespace wbr
