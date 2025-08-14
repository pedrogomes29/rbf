cmake_minimum_required(VERSION 3.0)

project(keydiff)

add_definitions(-DDEBUG)
add_library(murmurhash3 murmurhash3.cpp)
add_library(iblt iblt.cpp)
target_link_libraries(iblt murmurhash3)
add_library(utilstrencodings utilstrencodings.cpp)

add_executable(KeyDigest KeyDigest.cpp)
target_link_libraries(KeyDigest utilstrencodings iblt)

