// Read-only D435i metadata exporter. No stream start, option set, or calibration write.
// The caller owns power/USB/process prechecks and preserves stderr plus SDK logs.
#include <librealsense2/rs.hpp>
#include <librealsense2/hpp/rs_serializable_device.hpp>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <unistd.h>

namespace fs = std::filesystem;

std::string quote(const std::string& value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c);
        else out << c;
    }
    out << '"';
    return out.str();
}

template <class T> std::string array(const T* values, size_t count) {
    std::ostringstream out;
    out << std::setprecision(17) << '[';
    for (size_t i = 0; i < count; ++i) { if (i) out << ','; out << values[i]; }
    out << ']';
    return out.str();
}

std::string profile(const rs2::stream_profile& p) {
    std::ostringstream out;
    out << "\"uid\":" << p.unique_id() << ",\"stream\":" << quote(p.stream_name())
        << ",\"index\":" << p.stream_index() << ",\"format\":" << quote(rs2_format_to_string(p.format()))
        << ",\"fps\":" << p.fps();
    return out.str();
}

int main(int argc, char** argv) try {
    if (argc != 4 || std::string(argv[1]) != "--camera-available" ||
        std::string(argv[2]) != "243322073847" || geteuid() == 0)
        throw std::runtime_error("Usage (normal user): camera_metadata --camera-available 243322073847 NEW_DIRECTORY");
    const fs::path output(argv[3]);
    if (!fs::create_directory(output)) throw std::runtime_error("Output already exists");
    rs2::log_to_file(RS2_LOG_SEVERITY_INFO, (output / "sdk.log").string().c_str());
    rs2::context context(R"({"dds":{"enabled":false}})");
    auto devices = context.query_devices();
    if (devices.size() != 1) throw std::runtime_error("Expected exactly one SDK device");
    auto device = devices[0];
    if (std::string(device.get_info(RS2_CAMERA_INFO_SERIAL_NUMBER)) != argv[2])
        throw std::runtime_error("SDK serial mismatch");
    std::ofstream records(output / "metadata.jsonl");
    records.exceptions(std::ios::failbit | std::ios::badbit);
    records << std::setprecision(17);
    int errors = 0;
    auto error = [&](const std::string& operation, const std::exception& e) {
        ++errors;
        records << "{\"kind\":\"read_error\",\"operation\":" << quote(operation)
                << ",\"error\":" << quote(e.what()) << "}\n";
    };
    records << "{\"kind\":\"sdk_version\",\"header_api\":" << RS2_API_VERSION << "}\n";
    for (int i = 0; i < RS2_CAMERA_INFO_COUNT; ++i) {
        const auto info = static_cast<rs2_camera_info>(i);
        if (device.supports(info)) records << "{\"kind\":\"device_info\",\"name\":"
            << quote(rs2_camera_info_to_string(info)) << ",\"value\":" << quote(device.get_info(info)) << "}\n";
    }
    std::map<int, rs2::stream_profile> representatives;
    for (auto sensor : device.query_sensors()) {
        const std::string name(sensor.get_info(RS2_CAMERA_INFO_NAME));
        for (auto option : sensor.get_supported_options()) {
            try {
                const auto range = sensor.get_option_range(option);
                const auto value = sensor.get_option(option);
                const auto read_only = sensor.is_option_read_only(option);
                records << "{\"kind\":\"option\",\"sensor\":" << quote(name)
                    << ",\"name\":" << quote(rs2_option_to_string(option))
                    << ",\"value\":" << value << ",\"minimum\":" << range.min
                    << ",\"maximum\":" << range.max << ",\"step\":" << range.step
                    << ",\"default\":" << range.def << ",\"read_only\":" << (read_only ? "true" : "false") << "}\n";
            } catch (const std::exception& e) { error(name + "/" + rs2_option_to_string(option), e); }
        }
        for (auto p : sensor.get_stream_profiles()) {
            representatives.insert_or_assign(p.unique_id(), p);
            // Compose each row before writing so an SDK exception cannot leave partial JSON.
            std::ostringstream row;
            row << std::setprecision(17) << "{\"kind\":\"profile\",\"sensor\":" << quote(name) << ',' << profile(p);
            try {
                if (auto video = p.as<rs2::video_stream_profile>()) {
                    row << ",\"width\":" << video.width() << ",\"height\":" << video.height();
                    const auto k = video.get_intrinsics();
                    row << ",\"fx\":" << k.fx
                        << ",\"fy\":" << k.fy << ",\"ppx\":" << k.ppx << ",\"ppy\":" << k.ppy
                        << ",\"distortion\":" << quote(rs2_distortion_to_string(k.model))
                        << ",\"coefficients\":" << array(k.coeffs, 5);
                } else if (auto motion = p.as<rs2::motion_stream_profile>()) {
                    const auto k = motion.get_motion_intrinsics();
                    row << ",\"data_row_major_3x4\":[" << array(k.data[0], 4) << ',' << array(k.data[1], 4) << ',' << array(k.data[2], 4)
                        << "],\"noise_variances\":" << array(k.noise_variances, 3) << ",\"bias_variances\":" << array(k.bias_variances, 3);
                }
                records << row.str() << "}\n";
            } catch (const std::exception& e) {
                ++errors;
                records << row.str() << ",\"intrinsics_error\":" << quote(e.what()) << "}\n";
            }
        }
    }
    for (const auto& from : representatives) for (const auto& to : representatives) {
        try {
            const auto ex = from.second.get_extrinsics_to(to.second);
            records << "{\"kind\":\"extrinsics\",\"from_uid\":" << from.first << ",\"to_uid\":" << to.first
                << ",\"from_stream\":" << quote(from.second.stream_name()) << ",\"to_stream\":" << quote(to.second.stream_name())
                << ",\"rotation_column_major\":" << array(ex.rotation, 9) << ",\"translation_m\":" << array(ex.translation, 3) << "}\n";
        } catch (const std::exception& e) { error("extrinsics", e); }
    }
    try {
        auto serializable = device.as<rs2::serializable_device>();
        if (!serializable) throw std::runtime_error("Serializable extension unavailable");
        std::ofstream file(output / "advanced-settings.json");
        file.exceptions(std::ios::failbit | std::ios::badbit);
        file << serializable.serialize_json() << '\n';
    } catch (const std::exception& e) { error("read advanced settings", e); }
    try {
        auto calibration = device.as<rs2::auto_calibrated_device>();
        if (!calibration) throw std::runtime_error("Auto-calibrated read extension unavailable");
        const auto table = calibration.get_calibration_table();
        std::ofstream file(output / "active-calibration-table.bin", std::ios::binary);
        file.exceptions(std::ios::failbit | std::ios::badbit);
        file.write(reinterpret_cast<const char*>(table.data()), table.size());
        records << "{\"kind\":\"active_calibration_table\",\"bytes\":" << table.size()
                << ",\"scope\":\"SDK active table; not a complete EEPROM backup\"}\n";
    } catch (const std::exception& e) { error("read active calibration table", e); }
    records << "{\"kind\":\"completion\",\"read_errors\":" << errors << ",\"streams_started\":false,\"camera_writes\":false}\n";
    records.close();
    std::cout << "Metadata saved; read errors=" << errors << '\n';
    return errors ? 2 : 0;
} catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
}
