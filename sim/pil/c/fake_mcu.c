/* Fake MCU for host PIL tests: the same pil_core + wbr_lqr C code as the
 * Nucleo firmware, compiled for the Mac and served behind a pseudo-terminal.
 * Prints the slave device path on stdout, then serves frames until the host
 * side closes. The "cycle counter" is CLOCK_MONOTONIC nanoseconds (cpu_hz 1e9).
 */
#define _XOPEN_SOURCE 600
#define _DARWIN_C_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

#include "pil_core.h"

static int master = -1;

static void tx(void *ctx, const uint8_t *data, size_t n)
{
    (void)ctx;
    while (n) {
        ssize_t w = write(master, data, n);
        if (w < 0) {
            if (errno == EINTR)
                continue;
            exit(3);
        }
        data += w;
        n -= (size_t)w;
    }
}

static uint32_t cycles(void *ctx)
{
    (void)ctx;
#ifdef __APPLE__
    /* CLOCK_MONOTONIC is only microsecond-granular on macOS. */
    return (uint32_t)clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
#else
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (uint32_t)((uint64_t)t.tv_sec * 1000000000u + (uint64_t)t.tv_nsec);
#endif
}

int main(void)
{
    static pil_mcu mcu;
    pil_hooks hooks = {tx, cycles, NULL, NULL, 1000000000u};
    struct termios tio;
    uint8_t buf[256];
    const char *name;
    int slave;

    master = posix_openpt(O_RDWR | O_NOCTTY);
    if (master < 0 || grantpt(master) || unlockpt(master) || !(name = ptsname(master)))
        return 1;
    /* Hold the slave open in raw mode: no echo/line editing before the host's
     * serial library configures it, and no EIO when the host reopens. */
    slave = open(name, O_RDWR | O_NOCTTY);
    if (slave < 0 || tcgetattr(slave, &tio))
        return 1;
    cfmakeraw(&tio);
    if (tcsetattr(slave, TCSANOW, &tio))
        return 1;
    pil_mcu_init(&mcu, &hooks);
    printf("%s\n", name);
    fflush(stdout);
    for (;;) {
        ssize_t n = read(master, buf, sizeof(buf));
        if (n > 0)
            pil_mcu_feed(&mcu, buf, (size_t)n);
        else if (n < 0 && errno == EINTR)
            continue;
        else if (n == 0 || (n < 0 && errno != EIO))
            break;
        /* EIO without readers would spin; the held slave fd prevents it. */
    }
    fprintf(stderr, "fake_mcu: frames=%u errors=%u\n", mcu.frames, mcu.errors);
    return 0;
}
