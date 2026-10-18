CC ?= gcc
CFLAGS ?= -O3 -Wall -Wextra -fPIC -shared
TARGET_DIR ?= .

UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)

ifeq ($(UNAME_S),Darwin)
    TARGET = $(TARGET_DIR)/liblogparser.dylib
else ifeq ($(findstring MINGW,$(UNAME_S)),MINGW)
    TARGET = $(TARGET_DIR)/logparser.dll
    CFLAGS += -DBUILDING_LOGPARSER_DLL
else ifeq ($(findstring MSYS,$(UNAME_S)),MSYS)
    TARGET = $(TARGET_DIR)/logparser.dll
    CFLAGS += -DBUILDING_LOGPARSER_DLL
else ifeq ($(UNAME_S),Windows)
    TARGET = $(TARGET_DIR)/logparser.dll
    CFLAGS += -DBUILDING_LOGPARSER_DLL
else
    # Linux and other Unix systems
    TARGET = $(TARGET_DIR)/liblogparser.so
endif

all: $(TARGET)

$(TARGET): log_parser.c log_parser.h
	$(CC) $(CFLAGS) -o $@ log_parser.c

clean:
	rm -f $(TARGET_DIR)/liblogparser.so $(TARGET_DIR)/logparser.dll $(TARGET_DIR)/liblogparser.dylib *.o

.PHONY: all clean
