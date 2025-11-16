//
// Created by Kaeshev Alapati on 11/14/25.
//

#ifndef HACKRPI2025_FW_SIMPLE_SPI_H
#define HACKRPI2025_FW_SIMPLE_SPI_H
/*
 * datasheet https://www.displayfuture.com/Display/datasheet/controller/ST7735.pdf
 * clock write time = 66ns
 *  1 pulse   10^9 ns
 * -------- x --------  = 15.1515.. MHz
 *  66ns       1s
 */

#include "driver/gpio.h"
#include "driver/spi_master.h"

#define HARD_RESET_PIN GPIO_NUM_27

#define CS0_PIN  GPIO_NUM_5
#define SCLK_PIN GPIO_NUM_18
// #define MISO_PIN GPIO_NUM_19 not needed for only input device
#define MOSI_PIN GPIO_NUM_23
#define MODE_SELECT_PIN GPIO_NUM_16

#define CLOCK_WRITE_PERIOD_NS 66
#define SELECT_MODE_COMMAND 0
#define SELECT_MODE_DATA 1

#define CMD_SWRESET 0x01
#define CMD_SLPOUT  0x11
#define CMD_DISPON  0x29
#define CMD_COLMOD  0x3A

#define LEN_DATA_COLMOD 1
#define DATA_COLMOD (uint8_t[LEN_DATA_COLMOD]){0b101} // 16 bits per pixel mode

#define NUM_ROWS 128
#define NUM_COLS 128
#define BYTES_PER_PIXEL 2

#define CMD_CASET 0x2A
#define LEN_DATA_CASET 4
#define CASET_OFFSET 2
// format for data is min = [8 high bits, 8 low bits] + max = [8 high bits, 8 low bits]
#define DATA_CASET (uint8_t[LEN_DATA_CASET]) \
    {(0 + CASET_OFFSET) >> 8, (0 + CASET_OFFSET) & 0x00FF, \
    (NUM_COLS - 1 + CASET_OFFSET) >> 8, (NUM_COLS - 1 + CASET_OFFSET) & 0x00FF}

#define CMD_RASET 0x2B
#define LEN_DATA_RASET 4
#define RASET_OFFSET 2
#define DATA_RASET (uint8_t[LEN_DATA_RASET]) \
    {(0 + RASET_OFFSET) >> 8, (0 + RASET_OFFSET) & 0x00FF, \
    (NUM_ROWS - 1 + RASET_OFFSET) >> 8, (NUM_ROWS - 1 + RASET_OFFSET) & 0x00FF}

#define CMD_RAMWR 0x2C
#define LEN_DATA_RAMWR (NUM_ROWS*NUM_COLS*BYTES_PER_PIXEL) // 2 bytes per pixel, 128x128 pixels
#define LEN_LINE_RAMWR (NUM_COLS*BYTES_PER_PIXEL)     // one line 128 pixels * 2 bytes

extern spi_device_handle_t SPI_API;


void initialize_simple_spi();

void lcd_cmd(spi_device_handle_t spi, const uint8_t cmd, const uint16_t pause_in_ms);

void lcd_data(spi_device_handle_t spi, const uint8_t * data, uint16_t datalen, uint16_t pause_in_ms);

void draw_to_full_screen(spi_device_handle_t spi, const uint8_t * frame);

#endif //HACKRPI2025_FW_SIMPLE_SPI_H