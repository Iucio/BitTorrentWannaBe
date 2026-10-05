cmake_minimum_required(VERSION 3.16)
project(TrackerGPMS CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(SQLite3 REQUIRED)

add_library(tracker_core
    src/announce.cpp
    src/json.cpp
    src/repositorio.cpp
    src/repositorio_sqlite.cpp
    src/rotas.cpp
    src/servidor_http.cpp
    src/url.cpp
)
target_include_directories(tracker_core PUBLIC src)
target_link_libraries(tracker_core PUBLIC SQLite::SQLite3)

add_executable(tracker src/main.cpp)
target_link_libraries(tracker PRIVATE tracker_core)

enable_testing()
add_executable(teste_repositorio testes/teste_repositorio.cpp)
target_link_libraries(teste_repositorio PRIVATE tracker_core)
add_test(NAME repositorio COMMAND teste_repositorio)
