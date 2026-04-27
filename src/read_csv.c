// Read the EPFL ACM Frey CSV
#include "frey_concours.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[])
{
    const char *path = (argc > 1) ? argv[1] : "../Data/AcmEPFL.csv";
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); return -1; }

    char line[65536];
    int row = 0;
    size_t cap = INITIAL_ROWS;
    Entry *entries = malloc(cap * sizeof(Entry));
    if (!entries) { fclose(f); return -1; }

    /* skip header row */
    fgets(line, sizeof(line), f);

    while (fgets(line, sizeof(line), f)) {
	/* strip trailing \r\n */
	size_t n = strlen(line);
	while (n > 0 && (line[n-1] == '\n' || line[n-1] == '\r')) {
	    line[--n] = '\0';
	}

	/* grow array if needed */
	if ((size_t) row >= cap) {
	    cap *= 2;
	    Entry *tmp = realloc(entries, cap * sizeof(Entry));
	    if (!tmp) { perror("realloc"); break; }
	    entries = tmp;
	}

	memset(&entries[row], 0, sizeof(Entry));
	if (parse_csv_line(line, &entries[row]) > 0) {
	    row++;
	}
    }
    fclose(f);

    printf("Loaded %d entries.\n", row);

    /* use entries[] */
    for (int i=0; i<row; i++) {
	printf("%s\t:%s\n", entries[i].object_name, entries[i].artists);
    }

    /* Free entries */
    for (int i=0; i < row; i++) {
	free_entry(&entries[i]);
    }
    free(entries);
    return 0;
}
