# min, hour, dayOfMonth, month, dayOfWeek, command

# field         allowed values
# .....         ..............
# minute        0-59
# hour          0-23
# day of month  1-31
# month         1-12
# day of week   1-7        

#run a command every minute (every 10 minutes : 0 0/10 * 1/1 * ? *)
#* * * * * echo "Bonjours Noah" >> /app/result.output  2>&1

# min, hour, dayOfMonth, month, dayOfWeek, command

# Exécution tous les jours à 03:00 du matin pour éviter l'affluence du site
0 3 * * * cd /app && /usr/local/bin/python3 -u src/scraper.py 2>&1 | tee -a /app/data/cron.log > /proc/1/fd/1
