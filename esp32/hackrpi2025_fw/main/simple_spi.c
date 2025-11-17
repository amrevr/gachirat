//
// Created by Kaeshev Alapati on 11/14/25.
//
#include "simple_spi.h"
#include "driver/spi_master.h"
#include "string.h"
#include "freertos/task.h"
#include "esp_attr.h"


spi_device_handle_t SPI_API = {0};
spi_bus_config_t SPI_BUS_CONFIG = {0};
spi_device_interface_config_t SPI_SCREEN_INTERFACE_CONFIG = {0};

DMA_ATTR static uint8_t linebuf[LEN_LINE_RAMWR];


void lcd_cmd(spi_device_handle_t spi, const uint8_t cmd, uint16_t pause_in_ms) {
    gpio_set_level(MODE_SELECT_PIN, SELECT_MODE_COMMAND);

    esp_err_t ret;
    spi_transaction_t t = {0};
    t.length = 8; // Command is 8 bits
    t.tx_data[0] = cmd; // can use tx_data as our buffer
    t.flags = SPI_TRANS_USE_TXDATA;
    ret = spi_device_polling_transmit(spi, &t); //Transmit!
    assert(ret == ESP_OK); //Should have had no issues.
    if (pause_in_ms != 0) {
        vTaskDelay(pdMS_TO_TICKS(pause_in_ms)); // wait min n ms post sw reset
    }
}

void lcd_data(spi_device_handle_t spi, const uint8_t *data, uint16_t datalen, uint16_t pause_in_ms) {
    gpio_set_level(MODE_SELECT_PIN, SELECT_MODE_DATA);

    esp_err_t ret;
    spi_transaction_t t = {0};
    t.length = datalen * 8; // data is datalen bytes * 8 bits / byte
    if (datalen <= 4) {
        for (int i = 0; i < datalen; i++) {
            t.tx_data[i] = data[i];
        }
        t.flags = SPI_TRANS_USE_TXDATA;
    } else {
        t.tx_buffer = data;
        // tx buffer is used by default
    }

    ret = spi_device_polling_transmit(spi, &t); // Transmit!
    assert(ret == ESP_OK); // Should have had no issues.
    if (pause_in_ms != 0) {
        vTaskDelay(pdMS_TO_TICKS(pause_in_ms)); // wait min n ms post sw reset
    }
}


/** @brief initialize_simple_spi
 *  ✔ Software reset (SWRESET)
    ✔ Exit sleep (SLPOUT) — wait 120ms
    ✔ Set pixel format (COLMOD) → choose 16-bit
    ✔ Set memory access mode (MADCTL) → orientation
    ✔ Set CASET + RASET with correct offsets
    ✔ Turn display on (DISPON)
 */
void initialize_simple_spi() {
    esp_err_t ret;

    SPI_BUS_CONFIG.miso_io_num = -1;
    SPI_BUS_CONFIG.mosi_io_num = MOSI_PIN;
    SPI_BUS_CONFIG.sclk_io_num = SCLK_PIN;
    SPI_BUS_CONFIG.max_transfer_sz = 0;
    SPI_BUS_CONFIG.quadwp_io_num = -1;
    SPI_BUS_CONFIG.quadhd_io_num = -1;

    SPI_SCREEN_INTERFACE_CONFIG.clock_speed_hz = 15 * 1000 * 1000;
    SPI_SCREEN_INTERFACE_CONFIG.mode = 0;
    SPI_SCREEN_INTERFACE_CONFIG.spics_io_num = CS0_PIN;
    SPI_SCREEN_INTERFACE_CONFIG.queue_size = 4; // I don't plan to queue transactions but this is possible

    //Initialize the SPI bus
    ret = spi_bus_initialize(SPI3_HOST, &SPI_BUS_CONFIG, SPI_DMA_CH_AUTO);
    ESP_ERROR_CHECK(ret);

    //Attach the LCD to the SPI bus
    ret = spi_bus_add_device(SPI3_HOST, &SPI_SCREEN_INTERFACE_CONFIG, &SPI_API);
    ESP_ERROR_CHECK(ret);

    // GPIO Initialization (data/cmd input pin)
    gpio_set_direction(MODE_SELECT_PIN, GPIO_MODE_OUTPUT);
    gpio_set_level(MODE_SELECT_PIN, SELECT_MODE_DATA);

    // hardware reset init
    gpio_set_direction(HARD_RESET_PIN, GPIO_MODE_OUTPUT);
    gpio_set_level(HARD_RESET_PIN, 0);
    vTaskDelay(pdMS_TO_TICKS(300));
    gpio_set_level(HARD_RESET_PIN, 1);
    vTaskDelay(pdMS_TO_TICKS(300));


    //Initialize the LCD
    lcd_cmd(SPI_API, CMD_SWRESET, 150); // software reset

    lcd_cmd(SPI_API, CMD_SLPOUT, 150); // exit sleep

    lcd_cmd(SPI_API, CMD_COLMOD, 10); // init colors to 16 bits
    lcd_data(SPI_API, DATA_COLMOD, LEN_DATA_COLMOD, 1);

    lcd_cmd(SPI_API, CMD_DISPON, 150); // turn display on
}


/**
 * Draws a a frame to the screen
 * @param spi spi device handle
 * @param frame frame length of 128x128x2 is expected
 * @details rows 0->127*2, etc will be streamed
 */
void draw_to_full_screen(spi_device_handle_t spi, const uint8_t * frame) {
    // column range to 0->128
    lcd_cmd(spi, CMD_CASET, 1);
    lcd_data(spi, DATA_CASET, LEN_DATA_CASET, 1);

    // row range to 0->128
    lcd_cmd(spi, CMD_RASET, 1);
    lcd_data(spi, DATA_RASET, LEN_DATA_RASET, 1);

    lcd_cmd(spi, CMD_RAMWR, 0); // start transaction
    for (int row_num = 0; row_num < NUM_ROWS; row_num++) {
        const uint8_t * row_pointer = &frame[LEN_LINE_RAMWR * row_num];
        memcpy(linebuf, row_pointer, LEN_LINE_RAMWR);
        lcd_data(spi, linebuf, LEN_LINE_RAMWR, 0);
    }
}