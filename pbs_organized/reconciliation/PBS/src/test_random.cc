#include "random.h"
#include <iostream>

int main(int argc, char **argv) {
    size_t n = 10u;
    size_t s = 0u;
    if (argc == 2) n = std::stoul(argv[1]);
    else if (argc == 3) {
        n = std::stoul(argv[1]);
        s = std::stoul(argv[2]);
    }
    else if (argc > 3) {
        std::cerr << "Too many arguments. At most two are supported!\n";
        exit(1);
    }
    auto rarr = pbsutil::GenerateRandom32u(n, s);
    auto print = [](uint32_t a){
        std::cout << a << " ";
    };
    std::for_each(rarr.cbegin(), rarr.cend(), print);
    std::cout << "\n";
    return 0;
}