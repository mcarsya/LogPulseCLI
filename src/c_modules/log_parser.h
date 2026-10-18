/**
 * LogPulse CLI - High Performance C Log Parser
 * Memory Management: Manual heap allocation (malloc/calloc/realloc/free)
 * 
 * Provides fast line-by-line scanning and aggregation for large server log files.
 */

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

/**
 * C representation of aggregated log statistics.
 * Memory layout must match Python ctypes.Structure.
 */
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

/**
 * Parses a log file efficiently using chunked streaming and manual memory buffers.
 * @param filepath Path to the log file
 * @return Dynamically allocated LogStats pointer (must be freed with free_log_stats)
 */
LOGPARSER_API LogStats* parse_log_file(const char* filepath);

/**
 * Safely releases dynamically allocated memory for LogStats.
 * @param stats Pointer to LogStats allocated by parse_log_file
 */
LOGPARSER_API void free_log_stats(LogStats* stats);

/**
 * Streams and extracts only error and critical lines into a new destination file.
 * Returns number of filtered lines written, or -1 on failure.
 */
LOGPARSER_API int64_t filter_error_lines(const char* input_path, const char* output_path);

/**
 * Version query function to verify library linkage.
 */
LOGPARSER_API const char* get_c_parser_version(void);

#ifdef __cplusplus
}
#endif

#endif /* LOG_PARSER_H */
