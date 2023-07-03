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
python scripts/send_weekly_email.py >> .logs/weekly_email.log
```

