/* Host access to the same C receiver/model used in the ARM image. */
#include "twin.h"
#include <string.h>
static twin_link link;
static uint8_t output[8192];
static size_t output_n;
static twin_command last;
static uint32_t commands;
static void tx(void *ctx,const uint8_t *d,size_t n) {
 (void)ctx;
 if(output_n+n<=sizeof(output)) { memcpy(output+output_n,d,n); output_n+=n; }
}
static void command(void *ctx,const twin_command *c) { (void)ctx; last=*c; commands++; }
void h_init(void) { output_n=commands=0; twin_init(&link,123,tx,command,0); }
void h_feed(const uint8_t *d,size_t n,uint32_t now) { for(size_t i=0;i<n;i++) twin_feed(&link,d[i],now); }
void h_poll(uint32_t now) { twin_poll(&link,now); }
unsigned h_leds(void) { return twin_leds(&link); }
unsigned h_commands(void) { return commands; }
unsigned h_errors(void) { return link.parse_errors; }
void h_last(twin_command *c) { *c=last; }
size_t h_output(uint8_t *d) { size_t n=output_n; memcpy(d,output,n); output_n=0; return n; }
