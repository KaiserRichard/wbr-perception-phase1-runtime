// SYNTHETIC ONLY: directly exercises recorder counters with the local SDK stub.
#define ALLAN_RECORDER_TEST
#include "../d435i_imu_record.cpp"
#include <cassert>

int main() {
    Stats stats;
    const auto hardware = RS2_TIMESTAMP_DOMAIN_HARDWARE_CLOCK;
    const auto system = RS2_TIMESTAMP_DOMAIN_SYSTEM_TIME;
    stats.add(Sample{0, 1000.0, hardware, 1, 0, {}});
    stats.add(Sample{0, 1.0, system, 2, 0, {}});
    assert(stats.domain_changes == 1);
    assert(stats.backwards == 0);
    assert(stats.duplicates == 0);
    assert(stats.max_gap_ms == 0.0);

    stats.add(Sample{0, 2.0, system, 3, 0, {}});
    assert(stats.domain_changes == 1);
    assert(stats.backwards == 0);
    assert(stats.max_gap_ms == 1.0);

    stats.add(Sample{0, 2.0, system, 4, 0, {}});
    assert(stats.duplicates == 1);
}
