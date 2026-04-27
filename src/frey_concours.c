#include "frey_concours.h"
#include <stdlib.h>
#include <string.h>

int assign_field(Entry *e, int col_idx, const char *val) {
    // Take a parsed string and put it into the right struct field by column index:
    char *s = strdup(val);
    if (!s) return -1;
    switch (col_idx) {
	case  0: e->object_name		= s; break;
	case  1: e->category		= s; break;
	case  2: e->address_1		= s; break;
	case  3: e->address_2		= s; break;
	case  4: e->address_3		= s; break;
	case  5: e->postal_code		= s; break;
	case  6: e->locality		= s; break;
	case  7: e->canton_department	= s; break;
	case  8: e->country		= s; break;
	case  9: e->start_date		= s; break;
	case 10: e->end_date		= s; break;
	case 11: e->competition_open_until =s; break;
	case 12: e->notes		= s; break;
	case 13: e->artists		= s; break;
	case 14: e->artist_roles	= s; break;
	case 15: e->file_sources	= s; break;
	case 16: e->piece_sources	= s; break;
	default: free(s); break;
    }
    return 0;
}

void free_entry(Entry *e) { 
    free(e->object_name);	/* Nom de l'objet */
    free(e->category);	/* Simple categories. Not Common. */
    free(e->address_1); 	/* Address 1. Sometimes as in the case of Concours des ponts de Lausanne, there are multiple addresses. */
    free(e->address_2);
    free(e->address_3);
    free(e->postal_code);
    free(e->locality);	/* Locality. Usually the commune or city. */
    free(e->canton_department); /* The canton and the department. */
    free(e->country);	/* pays */
    free(e->start_date);	/* date debut */
    free(e->end_date);
    free(e->competition_open_until);
    free(e->notes);
    free(e->artists);
    free(e->artist_roles);
    free(e->file_sources); /* ACM File ID: "0148.04.0541", for example. */
    free(e->piece_sources);
}

int parse_csv_line(const char *line, Entry *e) {
    char buf[MAX_FIELD_LEN];
    int col, len;
    const char *p = line;
    col = 0;

    while (col < MAX_FIELDS) {
	len = 0;

	if (*p == '"') {
	    p++;	/* skip opening quote */
	    while (*p) {
		if (*p == '"') {
		    if (*(p+1) == '"') { /* escaped quote */
			buf[len++] = '"';
			p+=2;
		    } else {
			p++;
			break;
		    }
		} else {
		    buf[len++] = *p++;
		}
		if (len >= MAX_FIELD_LEN -1) break;
	    }
	} else {
	    while (*p && *p != ',') { 
		buf[len++] = *p++;
		if (len >= MAX_FIELD_LEN-1) break;
	    }
	}
	
	// Close the string
	buf[len] = '\0';
	if (assign_field(e, col, buf) != 0) return -1;
	col ++;

	if (*p ==',') p++;
	else break;
    }
    return col;
}
