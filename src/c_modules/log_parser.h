#ifndef LOG_PARSER_H
#define LOG_PARSER_H

#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32) || defined(_WIN64)
    #ifdef BUILDING_LOGPARSER_DLL
        #define LOGPARSER_API __declspec(dllexport)
    #else
        #define LOGPARSER_API __declspec(dllimport)
    #endif
#else
    #define LOGPARSER_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint64_t total_lines;
    uint64_t bytes_processed;
    uint32_t info_count;
    uint32_t warning_count;
    uint32_t error_count;
    uint32_t critical_count;
    uint32_t status_2xx;
    uint32_t status_3xx;
    uint32_t status_4xx;
    uint32_t status_5xx;
    double execution_time_ms;
    char last_error[256];
} LogStats;

LOGPARSER_API LogStats* parse_log_file(const char* filepath);
LOGPARSER_API void free_log_stats(LogStats* stats);
LOGPARSER_API int64_t filter_error_lines(const char* input_path, const char* output_path);
LOGPARSER_API const char* get_c_parser_version(void);

#ifdef __cplusplus
}
#endif

#endif
