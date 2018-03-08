#/usr/bin/env python

import os
from proc.core import find_processes
import smtplib
from email.mime.text import MIMEText
from email.parser import Parser

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

    if cumulative_percent > 80:
        # Take action at the 80% mark - we want to schedule an nginx restart
        action_taken = 'Scheduling at for restart'
    else:

        action_taken = 'No action taken'

    # Send ourselves an email - you will need an email template in cwd
    with open('mail_headers.txt') as fp:
         headers = Parser().parse(fp)
    msg = MIMEText(action_taken)
    msg['To'] = headers['To']
    msg['From'] = headers['From']

    msg['Subject'] = headers['Subject'].format(cumulative_percent)

    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()
