//
// Created by Kaeshev Alapati on 11/15/25.
//

#ifndef HACKRPI2025_FW_SIMPLE_ANIMATION_LIB_H
#define HACKRPI2025_FW_SIMPLE_ANIMATION_LIB_H

#include <stdint.h>


typedef struct {
    const uint8_t * const * frames;
    uint8_t frame_count;
} Animation;

typedef void (*FrameDecoderFuncPtrType)(const uint8_t * compressed_framebuf, uint8_t * decoded_framebuf);

typedef struct {
    const Animation * const * walk_up_table;
    const uint8_t walk_up_table_length;

    const Animation * const * walk_down_table;
    const uint8_t walk_down_table_length;

    const uint8_t starting_index;

    volatile const uint8_t * desired_state;
    volatile uint8_t * current_state;

    uint8_t frame_period_ms;

    FrameDecoderFuncPtrType frame_decoder_func;
} ANIMATION_TASK_ARGS;

void animation_task(void * arg);

#endif //HACKRPI2025_FW_SIMPLE_ANIMATION_LIB_H