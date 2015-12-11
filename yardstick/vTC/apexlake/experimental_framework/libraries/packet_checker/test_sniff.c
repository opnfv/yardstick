// Copyright (c) 2015 Intel Research and Development Ireland Ltd.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <pcap.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netinet/if_ether.h>

static int expected_tos = -1;
static int cmatch = 0;


/* 4 bytes IP address */
typedef struct ip_address
{
    u_char byte1;
    u_char byte2;
    u_char byte3;
    u_char byte4;
} ip_address;


/* IPv4 header */
typedef struct ip_header
{
    u_char      ver_ihl;
    u_char      tos;
    u_short     tlen;
    u_short     identification;
    u_short     flags_fo;
    u_char      ttl;
    u_char      proto;
    u_short     crc;
    ip_address  saddr;
    ip_address  daddr;
    u_int       op_pad;
} ip_header;


/* UDP header*/
typedef struct udp_header
{
    u_short    sport;          // Source port
    u_short    dport;          // Destination port
    u_short    len;            // Datagram length
    u_short    crc;            // Checksum
} udp_header;


/* Save results on file */
void save_and_exit(int sig)
{
    write_file();
	exit(0);
}


/*
 * This callback function is called for each received packet
 */
void stats_collection(u_char *useless,
                      const struct pcap_pkthdr* pkthdr,
                      const u_char* packet)
{
    ip_header *ih;
    udp_header *uh;
    u_int ip_len;
    ih = (ip_header *) (packet + 14);
    ip_len = (ih->ver_ihl & 0xf) * 4;
    u_char tos = ih->tos;
    // Counter update
    if(tos==expected_tos)
        cmatch ++;
}


int main(int argc,char **argv)
{ 
    int i;
    char *dev; 
    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t* descr;
    const u_char *packet;
    struct pcap_pkthdr hdr;
    struct ether_header *eptr;

    if(argc != 3)
    {
        fprintf(stdout,"Usage: %s interface_name expected_tos\n", argv[0]);
        exit(1);
    }

    expected_tos = atoi(argv[2]);

    /* Setup signal to stop the sniffer */
	signal(SIGTERM, save_and_exit);
	
    /* Take a device to read from */
    dev = argv[1];
    if(dev == NULL)
    {
        printf("%s\n",errbuf);
        exit(1);
    }

    /* Open device for reading */
    descr = pcap_open_live(dev, BUFSIZ, 0, -1, errbuf);
    if(descr == NULL)
    {
        printf("pcap_open_live(): %s\n", errbuf);
        exit(1);
    }

    /* Start the loop to be run for each packet */
    pcap_loop(descr, -1, stats_collection, NULL);
    return 0;
}


int write_file()
{
    FILE *f = fopen("packet_checker.res", "w");
    if (f == NULL)
    {
        printf("Error opening file!\n");
        exit(1);
    }
    fprintf(f, "%d\n", cmatch);
    fclose(f);
}
