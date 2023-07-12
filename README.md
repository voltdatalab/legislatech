# legislatech
Sistema de monitoramento das tramitações de proposições sobre qualquer termo.

### Roda todo mundo

```bash

python main.py 

```

### Roda apenas um bot pelo nome

```bash
nohup python -u projeto_runner.py "esg_bot" >> logs/esg_bot.log &
```

### (CRON) Envia emails no final de semana

```bash
python scripts/variable_send_email.py --limite 15 --past_days 7 --periodicidade "week" >> .logs/weekly_email.log
```

### (CRON) Envia emails todos os dias

```bash
python scripts/variable_send_email.py --limite 10 --past_days 1 --periodicidade "day" >> .logs/day_email.log
```

### (CRON) Envia emails todos os meses

```bash
python scripts/variable_send_email.py --limite 35 --past_days 30 --periodicidade "month" >> .logs/month_email.log
```

