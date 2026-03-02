#include <Arduino.h>
#include "driver/i2s.h"
#include <math.h>

// FireBeetle 2 ESP32-P4 v1.0 pins (your choice)
#define I2S_BCLK 33   // MAX98357A BCLK
#define I2S_LRC  32   // MAX98357A LRC/WS
#define I2S_DOUT 31   // MAX98357A DIN (data in to amp)

// Audio
static const int SAMPLE_RATE = 44100;
static const float TONE_HZ   = 440.0f;
static const float AMP       = 0.12f;   // start low (0.02..0.30)
static const i2s_port_t I2S_PORT = I2S_NUM_0;

static void i2s_begin() {
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = SAMPLE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT; // stereo
#if ESP_IDF_VERSION_MAJOR >= 5
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
#else
  cfg.communication_format = I2S_COMM_FORMAT_I2S_MSB;
#endif
  cfg.intr_alloc_flags = 0;
  cfg.dma_buf_count = 8;
  cfg.dma_buf_len = 256;
  cfg.use_apll = false;
  cfg.tx_desc_auto_clear = true;
  cfg.fixed_mclk = 0;

  esp_err_t e = i2s_driver_install(I2S_PORT, &cfg, 0, nullptr);
  if (e != ESP_OK) {
    Serial.printf("i2s_driver_install failed: %d\n", (int)e);
    return;
  }

  i2s_pin_config_t pins = {};
  pins.bck_io_num = I2S_BCLK;
  pins.ws_io_num  = I2S_LRC;
  pins.data_out_num = I2S_DOUT;
  pins.data_in_num  = I2S_PIN_NO_CHANGE;
#if ESP_IDF_VERSION_MAJOR >= 4
  pins.mck_io_num = I2S_PIN_NO_CHANGE; // MAX98357A doesn't need MCLK
#endif

  e = i2s_set_pin(I2S_PORT, &pins);
  if (e != ESP_OK) {
    Serial.printf("i2s_set_pin failed: %d\n", (int)e);
    return;
  }

  i2s_zero_dma_buffer(I2S_PORT);
  Serial.println("I2S begin OK");
}

static void write_tone_ms(float freq, int ms) {
  const int CHUNK_FRAMES = 256;              // stereo frames
  int16_t buf[CHUNK_FRAMES * 2];             // L,R interleaved
  static float phase = 0.0f;
  const float w = 2.0f * (float)M_PI * freq / (float)SAMPLE_RATE;

  int totalFrames = (SAMPLE_RATE * ms) / 1000;
  int sent = 0;

  while (sent < totalFrames) {
    int n = min(CHUNK_FRAMES, totalFrames - sent);

    for (int i = 0; i < n; i++) {
      int16_t s = (int16_t)(sinf(phase) * (AMP * 32767.0f));
      buf[2 * i + 0] = s; // L
      buf[2 * i + 1] = s; // R
      phase += w;
      if (phase > 2.0f * (float)M_PI) phase -= 2.0f * (float)M_PI;
    }

    size_t bytesWritten = 0;
    i2s_write(I2S_PORT, (const char*)buf, n * 2 * sizeof(int16_t), &bytesWritten, portMAX_DELAY);
    sent += n;

    yield(); // helps avoid watchdog resets on some builds
  }
}

static void write_silence_ms(int ms) {
  const int CHUNK_FRAMES = 256;
  int16_t zeros[CHUNK_FRAMES * 2] = {0};

  int totalFrames = (SAMPLE_RATE * ms) / 1000;
  int sent = 0;

  while (sent < totalFrames) {
    int n = min(CHUNK_FRAMES, totalFrames - sent);
    size_t bytesWritten = 0;
    i2s_write(I2S_PORT, (const char*)zeros, n * 2 * sizeof(int16_t), &bytesWritten, portMAX_DELAY);
    sent += n;
    yield();
  }
}

void setup() {
  Serial.begin(115200);
  delay(300);
  i2s_begin();
}

void loop() {
  Serial.println("MAX98357A I2S beep test");
  write_tone_ms(TONE_HZ, 400);
  write_silence_ms(400);
  delay(10);
}