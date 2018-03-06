#/usr/bin/env python

import os
from proc.core import find_processes


if __name__ == '__main__':
    page_size = os.sysconf('SC_PAGE_SIZE')
    physical_pages = os.sysconf('SC_PHYS_PAGES')
    total_mem = page_size * physical_pages
    print ('Page size = {}, pages = {}, total_mem = {} ({:.1f} MB)'.format(page_size,
                                                                    physical_pages,
                                                                    total_mem,
                                                                    total_mem / (1024**2)))


    nginx_processes = [x for x in find_processes() if x.comm == 'nginx' ]

    cumulative_percent = 0

    for x in nginx_processes:
        print ('nginx process pid = {}, parent_pid = {} , rss = {} '.format(x.pid,
                                                                            x.ppid,
                                                                            x.rss))

        process_percent = (x.rss / total_mem) * 100
        cumulative_percent = cumulative_percent + process_percent

    print ('Cumulative nginx memory use = ', cumulative_percent)