// Physical raw capture. SDK callbacks only enqueue; main thread owns all files.
// Run through run_precision.py after N2. No firmware or calibration writes.
#include <librealsense2/rs.hpp>
#include <atomic>
#include <chrono>
#include <cmath>
#include <csignal>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <thread>
#include <unistd.h>

namespace fs = std::filesystem;
using Steady = std::chrono::steady_clock;
volatile std::sig_atomic_t interrupted = 0;
void stop_signal(int) { interrupted = 1; }
template<class Clock> long long now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();
}
std::string quote(const std::string& s) {
    std::ostringstream o; o << '"';
    for (unsigned char c : s) {
        if (c == '"' || c == '\\') o << '\\' << c;
        else if (c < 32) o << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c);
        else o << c;
    }
    return o.str() + '"';
}
struct Item { rs2::frame frame; long long steady_ns; long long utc_ns; };
struct Sensor {
    rs2::sensor sensor;
    std::vector<rs2::stream_profile> profiles;
    bool opened = false, started = false;
};

int main(int argc, char** argv) try {
    if (argc != 6 || std::string(argv[1]) != "--camera-available" || geteuid() == 0)
        throw std::runtime_error("Usage: precision_capture --camera-available NEW_DIR SECONDS IMAGE_EVERY EMITTER_OFF_0_OR_1");
    const fs::path output(argv[2]);
    const int seconds = std::stoi(argv[3]), image_every = std::stoi(argv[4]);
    const bool emitter_off = std::string(argv[5]) == "1";
    if (seconds < 1 || seconds > 1800 || image_every < 0 ||
        (std::string(argv[5]) != "0" && !emitter_off)) throw std::runtime_error("Invalid bounds");
    if (!fs::create_directory(output)) throw std::runtime_error("Output must be new");
    fs::create_directory(output / "images");
    std::signal(SIGINT, stop_signal); std::signal(SIGTERM, stop_signal);
    rs2::log_to_file(RS2_LOG_SEVERITY_INFO, (output / "sdk.log").c_str());
    rs2::context context(R"({"dds":{"enabled":false}})");
    auto devices = context.query_devices();
    if (devices.size() != 1) throw std::runtime_error("Expected one physical SDK device");
    auto device = devices[0];
    if (std::string(device.get_info(RS2_CAMERA_INFO_SERIAL_NUMBER)) != "243322073847" ||
        std::string(device.get_info(RS2_CAMERA_INFO_FIRMWARE_VERSION)) != "5.17.3.10")
        throw std::runtime_error("Unexpected identity/firmware");
    std::ofstream rows(output / "frames.jsonl"), config(output / "configuration.jsonl");
    rows.exceptions(std::ios::failbit | std::ios::badbit);
    config.exceptions(std::ios::failbit | std::ios::badbit);
    rows << std::setprecision(17); config << std::setprecision(17);
    config << "{\"serial\":\"243322073847\",\"firmware\":\"5.17.3.10\",\"sdk_api\":" << RS2_API_VERSION
           << ",\"seconds\":" << seconds << ",\"image_every\":" << image_every << "}\n";
    std::vector<Sensor> sensors;
    int selected = 0;
    for (auto sensor : device.query_sensors()) {
        Sensor chosen{sensor, {}};
        for (auto p : sensor.get_stream_profiles()) {
            bool match = (p.stream_type() == RS2_STREAM_GYRO && p.fps() == 200 && p.format() == RS2_FORMAT_MOTION_XYZ32F) ||
                         (p.stream_type() == RS2_STREAM_ACCEL && p.fps() == 100 && p.format() == RS2_FORMAT_MOTION_XYZ32F);
            if (auto v = p.as<rs2::video_stream_profile>())
                match = p.stream_type() == RS2_STREAM_INFRARED && p.stream_index() == 1 && p.fps() == 15 &&
                        p.format() == RS2_FORMAT_Y8 && v.width() == 640 && v.height() == 480;
            if (match) { chosen.profiles.push_back(p); ++selected; }
        }
        if (!chosen.profiles.empty()) sensors.push_back(chosen);
    }
    if (selected != 3 || sensors.size() != 2) throw std::runtime_error("Exact three-profile selection failed");
    std::mutex mutex;
    std::deque<Item> queue;
    std::atomic<unsigned long long> overflow{0};
    std::atomic<bool> accepting{true};
    size_t high_water = 0;
    auto callback = [&](rs2::frame frame) {
        Item item{frame, now_ns<Steady>(), now_ns<std::chrono::system_clock>()};
        std::lock_guard<std::mutex> lock(mutex);
        if (!accepting) return;
        if (queue.size() >= 2048) { ++overflow; return; }
        queue.push_back(std::move(item));
        high_water = std::max(high_water, queue.size());
    };
    rs2::sensor emitter_sensor;
    float previous_emitter = 0;
    bool changed_emitter = false;
    auto cleanup = [&]() {
        accepting = false;
        for (auto& s : sensors) if (s.started) { s.sensor.stop(); s.started = false; }
        for (auto& s : sensors) if (s.opened) { s.sensor.close(); s.opened = false; }
        if (changed_emitter) { emitter_sensor.set_option(RS2_OPTION_EMITTER_ENABLED, previous_emitter); changed_emitter = false; }
    };
    unsigned long long count = 0, ir_count = 0;
    const auto begin = Steady::now();
    try {
        for (auto& s : sensors) {
            const auto name = s.sensor.get_info(RS2_CAMERA_INFO_NAME);
            if (emitter_off && s.sensor.supports(RS2_OPTION_EMITTER_ENABLED)) {
                previous_emitter = s.sensor.get_option(RS2_OPTION_EMITTER_ENABLED);
                emitter_sensor = s.sensor;
                s.sensor.set_option(RS2_OPTION_EMITTER_ENABLED, 0); changed_emitter = true;
                config << "{\"sensor\":" << quote(name) << ",\"emitter_before\":" << previous_emitter << ",\"emitter_during\":0}\n";
            }
            for (auto option : {RS2_OPTION_GLOBAL_TIME_ENABLED, RS2_OPTION_ENABLE_MOTION_CORRECTION,
                                RS2_OPTION_ASIC_TEMPERATURE, RS2_OPTION_PROJECTOR_TEMPERATURE}) {
                if (!s.sensor.supports(option)) continue;
                try {
                    const auto value = s.sensor.get_option(option);
                    config << "{\"sensor\":" << quote(name) << ",\"option\":" << quote(rs2_option_to_string(option)) << ",\"value\":" << value << "}\n";
                } catch (const std::exception& e) {
                    config << "{\"sensor\":" << quote(name) << ",\"option\":" << quote(rs2_option_to_string(option)) << ",\"read_error\":" << quote(e.what()) << "}\n";
                }
            }
            s.sensor.open(s.profiles); s.opened = true;
            s.sensor.start(callback); s.started = true;
        }
        config.flush();
        std::cout << "STREAMING_READY " << now_ns<std::chrono::system_clock>() << std::endl;
        const auto deadline = Steady::now() + std::chrono::seconds(seconds);
        bool stopped = false;
        while (true) {
            if (!stopped && (Steady::now() >= deadline || interrupted || overflow)) { cleanup(); stopped = true; }
            Item item;
            bool available;
            {
                std::lock_guard<std::mutex> lock(mutex);
                available = !queue.empty();
                if (available) { item = std::move(queue.front()); queue.pop_front(); }
            }
            if (!available) {
                if (stopped) break;
                std::this_thread::sleep_for(std::chrono::milliseconds(1)); continue;
            }
            const auto& f = item.frame;
            const auto p = f.get_profile();
            const double stamp = f.get_timestamp();
            if (!std::isfinite(stamp)) throw std::runtime_error("Nonfinite SDK timestamp");
            rows << "{\"stream\":" << quote(p.stream_name()) << ",\"frame_number\":" << f.get_frame_number()
                 << ",\"sdk_timestamp_ms\":" << stamp << ",\"timestamp_domain\":"
                 << quote(rs2_timestamp_domain_to_string(f.get_frame_timestamp_domain()))
                 << ",\"host_steady_ns\":" << item.steady_ns << ",\"host_utc_ns\":" << item.utc_ns;
            if (auto motion = f.as<rs2::motion_frame>()) {
                const auto xyz = motion.get_motion_data();
                if (!std::isfinite(xyz.x) || !std::isfinite(xyz.y) || !std::isfinite(xyz.z)) throw std::runtime_error("Nonfinite IMU");
                rows << ",\"xyz\":[" << xyz.x << ',' << xyz.y << ',' << xyz.z << ']';
            } else if (auto video = f.as<rs2::video_frame>()) {
                if (video.get_width() != 640 || video.get_height() != 480 || p.format() != RS2_FORMAT_Y8 || video.get_stride_in_bytes() < 640)
                    throw std::runtime_error("Malformed video frame");
                ++ir_count;
                if (image_every && (ir_count - 1) % image_every == 0) {
                    const auto name = "images/ir1-" + std::to_string(f.get_frame_number()) + ".pgm";
                    std::ofstream image(output / name, std::ios::binary); image.exceptions(std::ios::failbit | std::ios::badbit);
                    image << "P5\n640 480\n255\n";
                    for (int y = 0; y < 480; ++y) image.write(static_cast<const char*>(f.get_data()) + y * video.get_stride_in_bytes(), 640);
                    image.close(); rows << ",\"image\":" << quote(name);
                }
            }
            rows << ",\"metadata\":{";
            bool first = true;
            for (int i = 0; i < RS2_FRAME_METADATA_COUNT; ++i) {
                auto key = static_cast<rs2_frame_metadata_value>(i);
                if (!f.supports_frame_metadata(key)) continue;
                try {
                    const auto value = f.get_frame_metadata(key);
                    if (!first) rows << ',';
                    rows << quote(rs2_frame_metadata_to_string(key)) << ':' << value; first = false;
                } catch (const std::exception& e) {
                    if (!first) rows << ',';
                    rows << quote(std::string(rs2_frame_metadata_to_string(key)) + "_read_error") << ':' << quote(e.what()); first = false;
                }
            }
            rows << "}}\n";
            if (++count % 315 == 0) rows.flush();
        }
        rows.close(); config.close();
        std::ofstream result(output / "collector-result.json"); result.exceptions(std::ios::failbit | std::ios::badbit);
        result << "{\"frames\":" << count << ",\"ir_frames\":" << ir_count << ",\"queue_overflow\":" << overflow
               << ",\"queue_high_water\":" << high_water << ",\"interrupted\":" << (interrupted ? "true" : "false")
               << ",\"elapsed_seconds\":" << std::chrono::duration<double>(Steady::now()-begin).count() << ",\"clean_stop\":true}\n";
        std::cout << "CAPTURE_COMPLETE frames=" << count << " overflow=" << overflow << std::endl;
        return interrupted || overflow ? 1 : 0;
    } catch (...) { try { cleanup(); } catch (const std::exception& e) { std::cerr << "Cleanup: " << e.what() << '\n'; } throw; }
} catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
