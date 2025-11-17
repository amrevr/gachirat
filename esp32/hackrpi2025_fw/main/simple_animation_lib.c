//
// Created by Kaeshev Alapati on 11/15/25.
//
#include "simple_animation_lib.h"
#include <string.h>
#include "simple_spi.h"
#include "freertos/task.h"


static uint8_t DECODED_FRAMEBUFFER[LEN_DATA_RAMWR];


void animation_task(void * arg) {
    // decode the arguments
    ANIMATION_TASK_ARGS decoded_arg = *(ANIMATION_TASK_ARGS *)arg;
    uint8_t current_state = decoded_arg.starting_index;

    const FrameDecoderFuncPtrType frame_decoder_func = decoded_arg.frame_decoder_func;

    uint8_t frame_period_ms = decoded_arg.frame_period_ms;

    const Animation ** walk_up_table = decoded_arg.walk_up_table;
    uint8_t walk_up_table_length = decoded_arg.walk_up_table_length;

    const Animation ** walk_down_table = decoded_arg.walk_down_table;
    uint8_t walk_down_table_length = decoded_arg.walk_down_table_length;

    Animation current_animation = *walk_up_table[current_state];

    while (1) {
        *decoded_arg.current_state = current_state;
        // play animation
        for (uint8_t frame_index = 0; frame_index < current_animation.frame_count; frame_index++) {
            if (frame_decoder_func != NULL) {
                frame_decoder_func(current_animation.frames[frame_index], DECODED_FRAMEBUFFER);
                draw_to_full_screen(SPI_API, DECODED_FRAMEBUFFER);
            } else {
                draw_to_full_screen(SPI_API, current_animation.frames[frame_index]);
            }
            vTaskDelay(pdMS_TO_TICKS(frame_period_ms));
        }
        // switch animations if needed
        volatile uint8_t desired_state = *decoded_arg.desired_state;
        // if desired is more walk up the table until we hit desired
        if ((desired_state > current_state) && (desired_state < walk_up_table_length)) {
            current_state++;
            current_animation = *walk_up_table[current_state];
        // if desired is less walk down the table until we hit desired
        } else if ((desired_state < current_state) && (desired_state >= 0)) {
            current_state--;
            current_animation = *walk_down_table[current_state];
        }
    }
}
