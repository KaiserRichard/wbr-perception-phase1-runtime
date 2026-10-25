/* Example for the STM32 firmware owner; not compiled by this repository. */
#include <math.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "main.h" /* HAL_GetTick() */
#include "FreeRTOS.h"
#include "task.h"
#include "rcl/rcl.h"
#include "rclc/rclc.h"
#include "std_msgs/msg/float64_multi_array.h"

#define TERRAIN_ADVISORY_LEN 8U
#define TERRAIN_ADVISORY_STALE_MS 300U
enum { TERRAIN_NONE = 0, TERRAIN_JUMP = 1, TERRAIN_STOP = 2, TERRAIN_UNCERTAIN = 3 };

typedef struct {
  uint8_t code;
  double distance_m, height_m, width_m, confidence;
  bool plane_valid, received;
  uint64_t sequence;
  uint32_t received_tick;
  double detection_age_s; /* Pi diagnostic clock; never used for freshness. */
} TerrainAdvisory;

static rcl_subscription_t terrain_sub;
static double terrain_data[TERRAIN_ADVISORY_LEN];
static std_msgs__msg__Float64MultiArray terrain_msg;
static TerrainAdvisory latest_terrain;

static bool finite_array(const double *v) {
  for (size_t i = 0; i < TERRAIN_ADVISORY_LEN; ++i) if (!isfinite(v[i])) return false;
  return true;
}

static void terrain_callback(const void *msg_in) {
  const std_msgs__msg__Float64MultiArray *msg = msg_in;
  if (msg == NULL || msg->data.data == NULL || msg->data.size != TERRAIN_ADVISORY_LEN ||
      !finite_array(msg->data.data)) return;
  const double *v = msg->data.data;
  if (v[0] < 0 || v[0] > TERRAIN_UNCERTAIN || floor(v[0]) != v[0] ||
      v[4] < 0 || v[4] > 1 || (v[5] != 0 && v[5] != 1) || v[6] < 0 ||
      v[6] > 9007199254740991.0 || floor(v[6]) != v[6] || v[7] < 0) return;
  TerrainAdvisory next = {0};
  next.code = (uint8_t)v[0]; next.distance_m = v[1]; next.height_m = v[2];
  next.width_m = v[3]; next.confidence = v[4]; next.plane_valid = v[5] == 1;
  next.sequence = (uint64_t)v[6]; next.detection_age_s = v[7];
  next.received_tick = HAL_GetTick(); next.received = true;
  taskENTER_CRITICAL(); latest_terrain = next; taskEXIT_CRITICAL();
}

/* Call once during rclc setup; register terrain_callback with the executor. */
static rcl_ret_t terrain_subscription_init(rcl_node_t *node) {
  terrain_msg.data.data = terrain_data;
  terrain_msg.data.size = 0; terrain_msg.data.capacity = TERRAIN_ADVISORY_LEN;
  return rclc_subscription_init_best_effort(&terrain_sub, node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float64MultiArray), "/terrain_advisory");
}

static rcl_ret_t terrain_subscription_add_executor(rclc_executor_t *executor) {
  return rclc_executor_add_subscription(executor, &terrain_sub, &terrain_msg,
    terrain_callback, ON_NEW_DATA);
}

static TerrainAdvisory terrain_advisory_get(uint32_t now_tick) {
  TerrainAdvisory value;
  taskENTER_CRITICAL(); value = latest_terrain; taskEXIT_CRITICAL();
  if (!value.received || (uint32_t)(now_tick - value.received_tick) >= TERRAIN_ADVISORY_STALE_MS) {
    value = (TerrainAdvisory){0}; value.code = TERRAIN_UNCERTAIN;
  }
  return value;
}
