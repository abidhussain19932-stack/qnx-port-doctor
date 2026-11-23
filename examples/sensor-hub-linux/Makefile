CC = gcc
CFLAGS = -O2 -Wall
LDLIBS = -lpthread -lrt
sensor-hub: src/main.c
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)
