//
// Created by Kaeshev Alapati on 11/16/25.
//

#ifndef HACKRPI2025_FW_SIMPLE_WIFI_H
#define HACKRPI2025_FW_SIMPLE_WIFI_H

typedef struct {
    volatile uint8_t * desired_state_ptr;
} NETWORK_TASK_ARGS;

void configure_wifi(void);
void udp_receive_task(void *arg);

#endif //HACKRPI2025_FW_SIMPLE_WIFI_H