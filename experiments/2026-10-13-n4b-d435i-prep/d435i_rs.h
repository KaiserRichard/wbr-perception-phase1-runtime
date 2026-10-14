// Status: OPEN. Shared fixed stream selection and audit logging; SDK compile unverified.
#pragma once
#include <librealsense2/rs.hpp>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <ostream>
#include <stdexcept>
#include <string>

namespace wbr {
inline void streams(rs2::config& cfg) {
    cfg.disable_all_streams();
    cfg.enable_stream(RS2_STREAM_INFRARED, 1, 640, 480, RS2_FORMAT_Y8, 30);
    cfg.enable_stream(RS2_STREAM_INFRARED, 2, 640, 480, RS2_FORMAT_Y8, 30);
    cfg.enable_stream(RS2_STREAM_GYRO, RS2_FORMAT_MOTION_XYZ32F, 200);
    cfg.enable_stream(RS2_STREAM_ACCEL, RS2_FORMAT_MOTION_XYZ32F, 100);
}
inline void live_options(rs2::device dev, std::ostream& log) {
    bool emitter = false;
    for (auto sensor : dev.query_sensors()) {
        if (sensor.supports(RS2_OPTION_EMITTER_ENABLED)) {
            sensor.set_option(RS2_OPTION_EMITTER_ENABLED, 0);
            if (sensor.get_option(RS2_OPTION_EMITTER_ENABLED) != 0)
                throw std::runtime_error("emitter OFF readback failed");
            emitter = true;
        }
        // Preserve current global-time and motion-correction options; log them.
        // No persistent device/calibration changes or implicit global-time toggle.
        for (auto option : {RS2_OPTION_GLOBAL_TIME_ENABLED, RS2_OPTION_ENABLE_MOTION_CORRECTION})
            if (sensor.supports(option))
                log << sensor.get_info(RS2_CAMERA_INFO_NAME) << " " << option << "="
                    << sensor.get_option(option) << '\n';
    }
    if (!emitter) throw std::runtime_error("no emitter control; cannot attest OFF");
    log << "emitter=0 (read back before streaming)\n";
}
inline void verify(rs2::pipeline_profile profile, std::ostream& log) {
    const auto dev = profile.get_device();
    if (std::string(dev.get_info(RS2_CAMERA_INFO_SERIAL_NUMBER)) != "317422076650")
        throw std::runtime_error("wrong SDK device serial");
    log << "SDK serial=" << dev.get_info(RS2_CAMERA_INFO_SERIAL_NUMBER)
        << " firmware=" << dev.get_info(RS2_CAMERA_INFO_FIRMWARE_VERSION) << '\n';
    const auto profiles = profile.get_streams();
    if (profiles.size() != 4) throw std::runtime_error("expected exactly four streams");
    bool left=false, right=false, gyro=false, accel=false;
    for (auto p : profiles) {
        log << p.stream_name() << " index=" << p.stream_index() << " format="
            << p.format() << " fps=" << p.fps() << '\n';
        if (p.stream_type() == RS2_STREAM_INFRARED) {
            const auto v = p.as<rs2::video_stream_profile>();
            if (v.width()!=640 || v.height()!=480 || p.fps()!=30 || p.format()!=RS2_FORMAT_Y8)
                throw std::runtime_error("wrong IR profile");
            const auto k=v.get_intrinsics();
            log << std::setprecision(17) << "IR" << p.stream_index() << " intrinsics="
                << k.fx << ',' << k.fy << ',' << k.ppx << ',' << k.ppy << " distortion=" << k.model;
            for (float c : k.coeffs) log << ',' << c;
            log << '\n';
            if (std::abs(k.fx-386.953308105469)>1e-4 || std::abs(k.fy-386.953308105469)>1e-4 ||
                std::abs(k.ppx-321.034301757812)>1e-4 || std::abs(k.ppy-241.040130615234)>1e-4)
                throw std::runtime_error("IR projection differs from candidate calibration");
            for (float c : k.coeffs) if (std::abs(c)>1e-8)
                throw std::runtime_error("IR distortion differs from rectified candidate");
            if (p.stream_index()==1) left=true;
            else if (p.stream_index()==2) right=true;
        } else if (p.stream_type()==RS2_STREAM_GYRO)
            gyro = p.fps()==200 && p.format()==RS2_FORMAT_MOTION_XYZ32F;
        else if (p.stream_type()==RS2_STREAM_ACCEL)
            accel = p.fps()==100 && p.format()==RS2_FORMAT_MOTION_XYZ32F;
    }
    if (!(left && right && gyro && accel)) throw std::runtime_error("wrong stream set");
}
inline void stamp_header(std::ostream& out) {
    out << "stream,index,frame_number,sdk_ms,domain,host_steady_ns,host_utc_ns,x,y,z,exposure_us\n";
    out << std::setprecision(17);
}
inline void stamp(std::ostream& out, const rs2::frame& f) {
    const auto mono = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
    const auto utc = std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    out << f.get_profile().stream_name() << ',' << f.get_profile().stream_index()
        << ',' << f.get_frame_number() << ',' << f.get_timestamp() << ','
        << rs2_timestamp_domain_to_string(f.get_frame_timestamp_domain()) << ',' << mono << ',' << utc;
    if (auto m = f.as<rs2::motion_frame>()) {
        const auto v=m.get_motion_data(); out << ',' << v.x << ',' << v.y << ',' << v.z;
    } else out << ",,,";
    out << ',';
    if (f.supports_frame_metadata(RS2_FRAME_METADATA_ACTUAL_EXPOSURE))
        out << f.get_frame_metadata(RS2_FRAME_METADATA_ACTUAL_EXPOSURE);
    out << '\n';
    if (!out) throw std::runtime_error("timestamp audit write failed");
}
} // namespace wbr
