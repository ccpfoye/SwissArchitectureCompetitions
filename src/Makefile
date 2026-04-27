CC 	= gcc
CFLAGS 	= -Wall -Wextra -std=gnu11 -g

TARGET = read_csv
OBJS   = read_csv.o frey_concours.o


$(TARGET) : $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

read_csv.o: read_csv.c frey_concours.h
	$(CC) $(CFLAGS) -c $<

frey_concours.o: frey_concours.c frey_concours.h
	$(CC) $(CFLAGS) -c $<

clean:
	rm -f $(OBJS) $(TARGET)
