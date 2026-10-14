// First-party headless image check; never writes firmware, presets or calibration.
// The main thread owns pipeline/file lifetime; librealsense owns capture threads.
#include <librealsense2/rs.hpp>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unistd.h>

int main(int argc, char** argv) try {
    if (argc != 4 || std::string(argv[1]) != "--camera-available"
        || std::string(argv[2]) != "243322073847") {
        std::cerr << "Usage: sample_ir_checked --camera-available 243322073847 NEW_OUTPUT_DIRECTORY\n"
                  << "Only execute after current N1 and permission checks pass.\n";
        return 2;
    }
    if (geteuid() == 0) throw std::runtime_error("Run as normal camera user");
    const std::filesystem::path output(argv[3]);
    if (!std::filesystem::create_directory(output))
        throw std::runtime_error("Output directory must be new");
    rs2::log_to_console(RS2_LOG_SEVERITY_WARN);
    rs2::pipeline pipeline;
    rs2::config config;
    config.enable_device(argv[2]);
    config.disable_all_streams();
    config.enable_stream(RS2_STREAM_INFRARED, 1, 640, 480, RS2_FORMAT_Y8, 15);
    const auto active = pipeline.start(config);
    bool stopped = false;
    try {
        const auto profile = active.get_stream(RS2_STREAM_INFRARED, 1).as<rs2::video_stream_profile>();
        if (active.get_streams().size() != 1 || profile.width() != 640 || profile.height() != 480
            || profile.fps() != 15 || profile.format() != RS2_FORMAT_Y8)
            throw std::runtime_error("Unexpected active profile/extra stream");
        const auto intrinsics = profile.get_intrinsics();
        std::cout << std::setprecision(15) << "IR1 Y8 640x480 @15; fx=" << intrinsics.fx
                  << "; fy=" << intrinsics.fy << "; ppx=" << intrinsics.ppx << "; ppy=" << intrinsics.ppy
                  << "; distortion=" << rs2_distortion_to_string(intrinsics.model) << "\ncoefficients=";
        for (float value : intrinsics.coeffs) std::cout << value << ' ';
        std::cout << '\n';
        std::ofstream rows(output / "frames.csv");
        rows.exceptions(std::ios::failbit | std::ios::badbit);
        rows << "frame_number,stamp_ms,domain,width,height,stride,bytes,saved_file\n";
        int count = 0;
        double previous_stamp = -1;
        unsigned long long previous_number = 0;
        const auto start = std::chrono::steady_clock::now();
        while (std::chrono::steady_clock::now() - start < std::chrono::seconds(12)) {
            const auto frames = pipeline.wait_for_frames(3000);
            const auto frame = frames.get_infrared_frame(1);
            const int stride = frame.get_stride_in_bytes();
            const auto number = frame.get_frame_number();
            if (frame.get_width() != 640 || frame.get_height() != 480 || stride < 640
                || frame.get_data_size() != stride * 480 || frame.get_profile().format() != RS2_FORMAT_Y8)
                throw std::runtime_error("Malformed IR1 pixel buffer");
            const double stamp = frame.get_timestamp();
            if (!std::isfinite(stamp) || (count > 0 && (stamp <= previous_stamp
                || stamp - previous_stamp > 200.0 || number != previous_number + 1)))
                throw std::runtime_error("Invalid timestamp, gap or frame-number discontinuity");
            previous_stamp = stamp;
            previous_number = number;
            ++count;
            std::string filename;
            if (count == 30 || count == 90 || count == 150) {
                filename = "ir1-frame-" + std::to_string(count) + ".pgm";
                std::ofstream image(output / filename, std::ios::binary);
                image.exceptions(std::ios::failbit | std::ios::badbit);
                image << "P5\n640 480\n255\n";
                const auto pixels = static_cast<const char*>(frame.get_data());
                for (int y = 0; y < 480; ++y) image.write(pixels + y * stride, 640);
                image.close();
            }
            rows << number << ',' << std::setprecision(15) << stamp << ','
                 << rs2_timestamp_domain_to_string(frame.get_frame_timestamp_domain())
                 << ",640,480," << stride << ',' << frame.get_data_size() << ',' << filename << '\n';
        }
        rows.close();
        pipeline.stop();
        stopped = true;
        if (count < 150) throw std::runtime_error("Fewer than 150 frames; not all representatives saved");
        std::cout << "Frames checked=" << count << "; orderly stop\n";
    } catch (...) {
        if (!stopped) {
            try { pipeline.stop(); }
            catch (const std::exception& error) { std::cerr << "Shutdown failed: " << error.what() << '\n'; }
        }
        throw;
    }
    return 0;
} catch (const std::exception& error) {
    std::cerr << "IR content check failed: " << error.what() << '\n';
    return 1;
}
