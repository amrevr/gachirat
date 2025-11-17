#include <stdio.h>
#include "driver/spi_common.h"
#include "driver/spi_master.h"
#include "simple_spi.h"
#include "simple_animation_lib.h"
#include "simple_wifi.h"
#include "driver/uart.h"
#include "assets/NEUTRAL_frames.h"
#include "assets/HAPPY_frames.h"
#include "assets/SAD_frames.h"
#include "assets/IDLE_TO_SAD_frames.h"
#include "assets/SAD_TO_IDLE_frames.h"
#include "assets/IDLE_TO_HAPPY_frames.h"
#include "assets/HAPPY_TO_IDLE_frames.h"


// 16 bits per color, (r, g, b) (5, 6, 5) per the datasheet
#define RMAX ((1<<5) - 1)
#define GMAX ((1<<6) - 1)
#define BMAX ((1<<5) - 1)
#define RMIN 0
#define GMIN 0
#define BMIN 0

#define COMPRESSED_DATA_LENGTH_IN_BYTES (NUM_ROWS * NUM_COLS / 8)

typedef enum {
    ANGRY = 0,
    SAD,
    SAD_NEUTRAL_TRANSITION,
    NEUTRAL,
    HAPPY_NEUTRAL_TRANSITION,
    HAPPY,
    CELEBRATE,
    MAX_EMOTIONS
} EMOTIONS;

void decode_frame(const uint8_t * compressed_framebuf, uint8_t * decoded_framebuf);

static Animation sad_animation;
static Animation sad_to_neutral_animation;
static Animation neutral_to_sad_animation;
static Animation neutral_animation;
static Animation neutral_to_happy_animation;
static Animation happy_to_neutral_animation;
static Animation happy_animation;

static const Animation * const walk_up_table[] = {
    &sad_animation,
    &sad_to_neutral_animation,
    &neutral_animation,
    &neutral_to_happy_animation,
    &happy_animation
};

static const Animation * const walk_down_table[] = {
    &sad_animation,
    &neutral_to_sad_animation,
    &neutral_animation,
    &happy_to_neutral_animation,
    &happy_animation
};
volatile uint8_t desired_animation_state = 2;
volatile uint8_t current_animation_state = 2;

ANIMATION_TASK_ARGS animation_task_args = {
    .desired_state = &desired_animation_state,
    .frame_period_ms = 250,
    .walk_up_table = walk_up_table,
    .walk_up_table_length = 5,
    .walk_down_table = walk_down_table,
    .walk_down_table_length = 5,
    .current_state = &current_animation_state,
    .frame_decoder_func = decode_frame
};

typedef struct {
    uint8_t max_state;
    volatile uint8_t * desired_state_ptr;
    volatile const uint8_t * current_state;
} DUMMY_NETWORK_TASK_ARGS;

DUMMY_NETWORK_TASK_ARGS read_network_task_args = {.max_state = 4, &desired_animation_state, &current_animation_state};

NETWORK_TASK_ARGS read_network_task = { .desired_state_ptr = &desired_animation_state};

// void read_network_task(void * arg) {
//     NETWORK_TASK_ARGS * network_task_args = (NETWORK_TASK_ARGS *) arg;
//     int8_t desired_state = 4;
//     while (1) {
//         uint8_t current_state = *network_task_args->current_state;
//         if (current_state == 4) {
//             desired_state = 0;
//         } else if (current_state == 0) {
//             desired_state = 4;
//         }
//         *network_task_args->desired_state_ptr = desired_state;
//         printf("desired state %d, current state %d\n", desired_state, current_state);
//         vTaskDelay(pdMS_TO_TICKS(15000));
//     }
// }

void app_main(void)
{
    sad_animation.frames = SAD_ANIMATION;
    sad_animation.frame_count = SAD_ANIMATION_LEN;

    sad_to_neutral_animation.frames = SAD_TO_IDLE_ANIMATION;
    sad_to_neutral_animation.frame_count = SAD_TO_IDLE_ANIMATION_LEN;

    neutral_to_sad_animation.frames = IDLE_TO_SAD_ANIMATION;
    neutral_to_sad_animation.frame_count = IDLE_TO_SAD_ANIMATION_LEN;

    neutral_animation.frames = NEUTRAL_ANIMATION;
    neutral_animation.frame_count = NEUTRAL_ANIMATION_LEN;

    neutral_to_happy_animation.frames = IDLE_TO_HAPPY_ANIMATION;
    neutral_to_happy_animation.frame_count = IDLE_TO_HAPPY_ANIMATION_LEN;

    happy_to_neutral_animation.frames = HAPPY_TO_IDLE_ANIMATION;
    happy_to_neutral_animation.frame_count = HAPPY_TO_IDLE_ANIMATION_LEN;

    happy_animation.frames = HAPPY_ANIMATION;
    happy_animation.frame_count = HAPPY_ANIMATION_LEN;

    printf("initializing spi screen\n");
    initialize_simple_spi();
    printf("initializing wifi\n");
    configure_wifi();
    printf("starting animation task\n");
    xTaskCreate(animation_task, "animation_task", 4096, &animation_task_args, 5, NULL);
    printf("starting network task \n");
    xTaskCreate(udp_receive_task, "read_network_task", 4096, &read_network_task, 5, NULL);
}

void decode_frame(const uint8_t * compressed_framebuf, uint8_t * decoded_framebuf) {
    for (int compressed_byte_index = 0;
        compressed_byte_index < COMPRESSED_DATA_LENGTH_IN_BYTES;
        compressed_byte_index++) {
        // iterate downwards through the bits
        for (int bit_index = 7; bit_index >= 0; bit_index--) {
            // compressed byte 0 -> bytes 0 to 15 (spans 16)
            // compressed bit 0 -> bytes 1->2 (spans 2)
            uint16_t uncompressed_byte_index = compressed_byte_index * 16 + (7 - bit_index) * 2;
            bool bit = compressed_framebuf[compressed_byte_index] >> bit_index & 0b01;
            // if bit is 0, buffer will be (r=11111, b=111111, g=11111) -> (FF, FF) -> white
            // if bit is 1, buffer will be (r=0, b=0, g=0) -> (00, 00) -> black
            decoded_framebuf[uncompressed_byte_index + 1] = 0xFF * !bit;
            decoded_framebuf[uncompressed_byte_index] = 0xFF * !bit;
        }
    }
}
