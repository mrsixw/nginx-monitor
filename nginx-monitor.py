#/usr/bin/env python

import os
from proc.core import find_processes
import smtplib
from email.mime.text import MIMEText
from email.parser import Parser
import subprocess
from datetime import datetime, timedelta

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

    if cumulative_percent > 0:
        # Take action at the 80% mark - we want to schedule an nginx restart
        action_taken = 'Scheduling at for restart'

        # Check if we aleready have a restart pending
        at_query = subprocess.run(['atq','-q','s'],stdout=subprocess.PIPE)
        if at_query.returncode == 0:
            print(at_query.stdout.decode("utf-8"))

            # For now, if the length of the output was anything other than zero, we'll assumne somehting is
            # scheduled
            if len(at_query.stdout.decode("utf-8")) == 0:

                print("Job not scheduled")
                action_taken += "\n Job not scheduled - scheduling"


                tomorrow = datetime.now() + timedelta(days=1)

                print (tomorrow.date())

                timespec = "{}{}{}0930".format(tomorrow.date().year,
                                               tomorrow.date().month,
                                               tomorrow.date().day)

                sched_proc = subprocess.run(['echo','"systemctl restart nginx"','|','at','-q','s','-mv','-t',timespec],
                                             stdout=subprocess.PIPE)
            else:
                print("Job already scheduled")
                action_taken += "\n Job already scheduled in the at s queue - abort"

        else:
            action_taken += "\nReturn code from atq ({}) was {}".format(at_query.cmd,
                                                                        at_query.returncode)


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
