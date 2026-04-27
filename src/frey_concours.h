# ifndef FREY_CONCOURS_H
# define FREY_CONCOURS_H

#define MAX_LINE_LEGNTH 8192
#define MAX_FIELD_LEN 4096 
#define MAX_FIELDS 17
#define INITIAL_ROWS 2048

typedef struct {
    char *object_name;	/* Nom de l'objet */
    char *category;	/* Simple categories. Not Common. */
    char *address_1; 	/* Address 1. Sometimes (as in the case of Concours des ponts de Lausanne, there are multiple addresses. */
    char *address_2;
    char *address_3;
    char *postal_code;
    char *locality;	/* Locality. Usually the commune or city. */
    char *canton_department; /* The canton and the department. */
    char *country;	/* pays */
    char *start_date;	/* date debut */
    char *end_date;
    char *competition_open_until;
    char *notes;
    char *artists;
    char *artist_roles;
    char *file_sources; /* ACM File ID: "0148.04.0541", for example. */
    char *piece_sources;
} Entry;

int assign_field(Entry *e, int col_idx, const char *val);
void free_entry(Entry *e);
int parse_csv_line(const char *line, Entry *e);
# endif
