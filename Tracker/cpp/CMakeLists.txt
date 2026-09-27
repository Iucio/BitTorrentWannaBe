cmake_minimum_required(VERSION 3.16)
project(TrackerGPMS CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(tracker_core
    src/announce.cpp
    src/json.cpp
    src/repositorio.cpp
    src/rotas.cpp
    src/servidor_http.cpp
    src/url.cpp
)
target_include_directories(tracker_core PUBLIC src)

add_executable(tracker src/main.cpp)
target_link_libraries(tracker PRIVATE tracker_core)
