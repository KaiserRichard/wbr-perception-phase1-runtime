// Status: OPEN. Future Pi-only recorder; no camera execution or SDK build on Mac.
#include "d435i_rs.h"
#include <csignal>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <mutex>
#include <thread>

namespace { volatile std::sig_atomic_t running = 1;
void stop(int) { running = 0; } }

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "Usage: d435i_record NEW_OUTPUT_DIRECTORY SECONDS (1..120)\n";
        return 2;
    }
    try {
        std::size_t used=0;
        const double seconds=std::stod(argv[2], &used);
        if (used!=std::string(argv[2]).size() || !std::isfinite(seconds) || seconds<1 || seconds>120)
            throw std::runtime_error("duration must be 1..120 seconds");
        const std::filesystem::path dir(argv[1]);
        if (!std::filesystem::create_directory(dir))
            throw std::runtime_error("output directory must be new; parent must already exist");
        std::ofstream audit(dir/"timestamps.csv");
        if (!audit) throw std::runtime_error("cannot create timestamp audit");
        wbr::stamp_header(audit);
        rs2::log_to_file(RS2_LOG_SEVERITY_INFO, (dir/"sdk.log").string().c_str());
        std::signal(SIGINT, stop);
        std::signal(SIGTERM, stop);
        rs2::pipeline pipe;
        rs2::config cfg;
        wbr::streams(cfg);
        cfg.enable_device("317422076650");
        cfg.enable_record_to_file((dir/"stereo_imu.db3"  /* librealsense >=2.56 records rosbag2 .db3 */).string());
        auto resolved=cfg.resolve(pipe);
        wbr::verify(resolved, std::cout);
        wbr::live_options(resolved.get_device(), std::cout);
        std::mutex mutex;
        std::string error;
        unsigned long left=0, right=0, gyro=0, accel=0;
        auto callback = [&](const rs2::frame& frame) {
            std::lock_guard<std::mutex> lock(mutex);
            if (!error.empty()) return;
            try {
                if (auto fs=frame.as<rs2::frameset>()) {
                    for (const auto& f : fs) {
                        wbr::stamp(audit, f);
                        if (f.get_profile().stream_type()==RS2_STREAM_INFRARED) {
                            if (f.get_profile().stream_index()==1) ++left;
                            if (f.get_profile().stream_index()==2) ++right;
                        }
                    }
                } else {
                    wbr::stamp(audit, frame);
                    if (frame.get_profile().stream_type()==RS2_STREAM_GYRO) ++gyro;
                    if (frame.get_profile().stream_type()==RS2_STREAM_ACCEL) ++accel;
                }
            } catch (const std::exception& e) { error=e.what(); }
        };
        pipe.start(cfg, callback);
        const auto begin=std::chrono::steady_clock::now();
        while (running && std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()<seconds) {
            { std::lock_guard<std::mutex> lock(mutex); if (!error.empty()) break; }
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        pipe.stop(); // Normal shutdown finalizes the librealsense bag; no forced kill.
        audit.flush();
        std::cout << "callback counts IR1=" << left << " IR2=" << right
                  << " gyro=" << gyro << " accel=" << accel << '\n';
        if (!error.empty()) throw std::runtime_error(error);
        if (!audit || !left || !right || !gyro || !accel)
            throw std::runtime_error("missing stream or audit flush failure");
        std::cout << "OPEN: recorded; decode/count/timing/storage qualification still required\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "OPEN: recorder error: " << e.what() << '\n';
        return 1;
    }
}
