#define BUILDING_LOGPARSER_DLL
#include "log_parser.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>

#define CHUNK_BUFFER_SIZE (64 * 1024)
#define INITIAL_LINE_CAPACITY 1024
#define C_PARSER_VERSION "1.2.0-native"

LOGPARSER_API const char* get_c_parser_version(void) {
    return C_PARSER_VERSION;
}

static int contains_token_ci(const char* line, const char* token) {
    if (!line || !token) return 0;
    size_t token_len = strlen(token);
    size_t line_len = strlen(line);
    if (token_len > line_len) return 0;

    for (size_t i = 0; i <= line_len - token_len; i++) {
        size_t j = 0;
        while (j < token_len && tolower((unsigned char)line[i + j]) == tolower((unsigned char)token[j])) {
            j++;
        }
        if (j == token_len) {
            return 1;
        }
    }
    return 0;
}

static void inspect_status_code(const char* line, LogStats* stats) {
    const char* p = line;
    while (*p) {
        if ((*p == ' ' || *p == '"' || *p == '[') && isdigit((unsigned char)*(p + 1))) {
            const char* num_start = p + 1;
            if (isdigit((unsigned char)num_start[0]) &&
                isdigit((unsigned char)num_start[1]) &&
                isdigit((unsigned char)num_start[2]) &&
                (num_start[3] == ' ' || num_start[3] == '\r' || num_start[3] == '\n' || num_start[3] == '\0' || num_start[3] == '"')) {
                
                int code = (num_start[0] - '0') * 100 + (num_start[1] - '0') * 10 + (num_start[2] - '0');
                if (code >= 200 && code <= 299) {
                    stats->status_2xx++;
                    break;
                } else if (code >= 300 && code <= 399) {
                    stats->status_3xx++;
                    break;
                } else if (code >= 400 && code <= 499) {
                    stats->status_4xx++;
                    break;
                } else if (code >= 500 && code <= 599) {
                    stats->status_5xx++;
                    break;
                }
            }
        }
        p++;
    }
}

static void process_line(const char* line, LogStats* stats) {
    if (!line || !stats) return;

    stats->total_lines++;

    if (contains_token_ci(line, "CRITICAL") || contains_token_ci(line, "FATAL") || contains_token_ci(line, "[CRIT]")) {
        stats->critical_count++;
    } else if (contains_token_ci(line, "ERROR") || contains_token_ci(line, "[ERR]") || contains_token_ci(line, "EXCEPTION")) {
        stats->error_count++;
    } else if (contains_token_ci(line, "WARN") || contains_token_ci(line, "[WARN]") || contains_token_ci(line, "WARNING")) {
        stats->warning_count++;
    } else if (contains_token_ci(line, "INFO") || contains_token_ci(line, "[INFO]")) {
        stats->info_count++;
    }

    inspect_status_code(line, stats);
}

LOGPARSER_API LogStats* parse_log_file(const char* filepath) {
    if (!filepath) return NULL;

    LogStats* stats = (LogStats*)calloc(1, sizeof(LogStats));
    if (!stats) {
        return NULL;
    }

    clock_t start_clock = clock();

    FILE* fp = fopen(filepath, "rb");
    if (!fp) {
        snprintf(stats->last_error, sizeof(stats->last_error), "Failed to open file: %s", filepath);
        return stats;
    }

    char* chunk_buf = (char*)malloc(CHUNK_BUFFER_SIZE);
    if (!chunk_buf) {
        fclose(fp);
        snprintf(stats->last_error, sizeof(stats->last_error), "Memory allocation failed for chunk buffer");
        return stats;
    }

    size_t line_cap = INITIAL_LINE_CAPACITY;
    char* line_buf = (char*)malloc(line_cap);
    if (!line_buf) {
        free(chunk_buf);
        fclose(fp);
        snprintf(stats->last_error, sizeof(stats->last_error), "Memory allocation failed for line buffer");
        return stats;
    }

    size_t line_len = 0;
    size_t bytes_read = 0;

    while ((bytes_read = fread(chunk_buf, 1, CHUNK_BUFFER_SIZE, fp)) > 0) {
        stats->bytes_processed += bytes_read;

        for (size_t i = 0; i < bytes_read; i++) {
            char ch = chunk_buf[i];

            if (ch == '\n') {
                line_buf[line_len] = '\0';
                process_line(line_buf, stats);
                line_len = 0;
            } else if (ch != '\r') {
                if (line_len + 1 >= line_cap) {
                    size_t new_cap = line_cap * 2;
                    char* resized = (char*)realloc(line_buf, new_cap);
                    if (!resized) {
                        line_buf[line_len] = '\0';
                        process_line(line_buf, stats);
                        line_len = 0;
                        break;
                    }
                    line_buf = resized;
                    line_cap = new_cap;
                }
                line_buf[line_len++] = ch;
            }
        }
    }

    if (line_len > 0) {
        line_buf[line_len] = '\0';
        process_line(line_buf, stats);
    }

    free(line_buf);
    free(chunk_buf);
    fclose(fp);

    clock_t end_clock = clock();
    stats->execution_time_ms = ((double)(end_clock - start_clock) / CLOCKS_PER_SEC) * 1000.0;

    return stats;
}

LOGPARSER_API void free_log_stats(LogStats* stats) {
    if (stats) {
        free(stats);
    }
}

LOGPARSER_API int64_t filter_error_lines(const char* input_path, const char* output_path) {
    if (!input_path || !output_path) return -1;

    FILE* in_fp = fopen(input_path, "r");
    if (!in_fp) return -1;

    FILE* out_fp = fopen(output_path, "w");
    if (!out_fp) {
        fclose(in_fp);
        return -1;
    }

    size_t buf_cap = 4096;
    char* line = (char*)malloc(buf_cap);
    if (!line) {
        fclose(in_fp);
        fclose(out_fp);
        return -1;
    }

    int64_t matched_count = 0;

    while (fgets(line, (int)buf_cap, in_fp)) {
        if (contains_token_ci(line, "ERROR") || 
            contains_token_ci(line, "CRITICAL") || 
            contains_token_ci(line, "FATAL") ||
            contains_token_ci(line, "EXCEPTION") ||
            contains_token_ci(line, " 500 ") ||
            contains_token_ci(line, " 502 ") ||
            contains_token_ci(line, " 503 ") ||
            contains_token_ci(line, " 504 ")) {
            fputs(line, out_fp);
            matched_count++;
        }
    }

    free(line);
    fclose(in_fp);
    fclose(out_fp);

    return matched_count;
}
