cmake_minimum_required(VERSION 3.16)
project(TrackerGPMS CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(SQLite3 QUIET)
if(NOT SQLite3_FOUND)
    # SQLite não instalado (comum no Windows): baixa o código oficial e compila junto
    enable_language(C)
    include(FetchContent)
    if(POLICY CMP0135)
        cmake_policy(SET CMP0135 NEW)
    endif()
    # o http é reserva para cmake sem certificados, o hash garante o arquivo certo
    FetchContent_Declare(sqlite
        URL https://www.sqlite.org/2026/sqlite-amalgamation-3530400.zip
            http://www.sqlite.org/2026/sqlite-amalgamation-3530400.zip
        URL_HASH SHA256=1e71ddf93849c6a6ecf58b827c0692073d2dd7ee40196158068f7b29f422e87d)
    FetchContent_MakeAvailable(sqlite)
    find_package(Threads REQUIRED)
    add_library(sqlite3_embutido STATIC ${sqlite_SOURCE_DIR}/sqlite3.c)
    target_include_directories(sqlite3_embutido PUBLIC ${sqlite_SOURCE_DIR})
    target_link_libraries(sqlite3_embutido PUBLIC Threads::Threads ${CMAKE_DL_LIBS})
    add_library(SQLite::SQLite3 ALIAS sqlite3_embutido)
endif()

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
if(WIN32)
    target_link_libraries(tracker_core PUBLIC ws2_32) # Winsock: sockets do Windows
endif()

add_executable(tracker src/main.cpp)
target_link_libraries(tracker PRIVATE tracker_core)

enable_testing()
add_executable(teste_repositorio testes/teste_repositorio.cpp)
target_link_libraries(teste_repositorio PRIVATE tracker_core)
add_test(NAME repositorio COMMAND teste_repositorio)
