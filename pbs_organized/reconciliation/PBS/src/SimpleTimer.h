#ifndef __SIMPLETIMER_H_
#define __SIMPLETIMER_H_

#include <chrono>

struct SimpleTimer {
  void restart();
  std::chrono::nanoseconds elapsed();
private:
  std::chrono::high_resolution_clock::time_point _start;
};

void SimpleTimer::restart() {
    _start = std::chrono::high_resolution_clock::now();
}

std::chrono::nanoseconds SimpleTimer::elapsed() {
    auto cur = std::chrono::high_resolution_clock::now();
    return std::chrono::duration_cast<std::chrono::nanoseconds>(cur - _start);
}

#endif // __SIMPLETIMER_H_