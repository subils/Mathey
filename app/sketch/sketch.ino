// Mentor Cangur: el microcontrolador només pinta a la matriu de LEDs 8x13 el
// dibuix que li envia el Python (python/main.py) pel Bridge. Tot el que es
// mostra es decideix al Python.
//
// Copiat del patró de l'exemple oficial d'Arduino
// core-and-foundational/02-led-matrix/02-led-matrix-frame (MPL-2.0).

#include <Arduino_RouterBridge.h>
#include <Arduino_LED_Matrix.h>
#include <vector>

Arduino_LED_Matrix matrix;

const uint8_t FRAME_ROWS = 8;
const uint8_t FRAME_COLS = 13;
const uint8_t FRAME_SIZE = FRAME_ROWS * FRAME_COLS;

uint8_t frame[FRAME_SIZE] = {0};

// El Python crida Bridge.call("draw", bytes): 104 valors de brillantor 0-7, per files.
void draw(std::vector<uint8_t> newFrame) {
    size_t len = min(newFrame.size(), (size_t)FRAME_SIZE);
    memcpy(frame, newFrame.data(), len);
}

void setup() {
    matrix.begin();
    matrix.setGrayscaleBits(3);  // brillantor 0-7
    matrix.clear();
    Bridge.begin();
    Bridge.provide("draw", draw);
}

void loop() {
    matrix.draw(frame);
    delay(10);
}
